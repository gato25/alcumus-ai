"""Read the problem Alcumus is currently serving your account.

The statement is not fetched over XHR — AoPS embeds it in the page bootstrap at
`window.AoPS.bootstrap_data.alc_init_data.user.current_problem`, where
`problem_text_bbcode` holds the clean LaTeX source. That is the primary path.

Two fallbacks exist because AoPS moves things: any JSON response that scores as
a problem, then scraping the rendered node. Scraping needs care — AoPS renders
math as `<img class="latex" alt="$x^2$">`, so `innerText` silently drops every
equation. `html_to_latex` restores it from the alt attributes.
"""

from __future__ import annotations

import html as html_lib
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Iterator

from playwright.sync_api import BrowserContext, Error as PlaywrightError, Page, Response

from .config import PROBLEM_URL, capture_log
from .models import Problem
from .session import NotLoggedIn, browser_context, is_challenge, looks_logged_out
from .session import CloudflareChallenge as CloudflareChallenge  # re-export

# A JSON payload must score at least this well to be treated as "the problem".
PROBLEM_SCORE = 6

_ASSET = re.compile(r"\.(js|mjs|css|png|jpe?g|gif|svg|woff2?|ico|map|ttf)(\?|$)", re.I)
_TEXT_KEY = re.compile(
    r"(problem|question|statement|prompt)(_?(text|html|body|latex|bbcode))?$|^(text|html|latex)$",
    re.I,
)
_HINT_KEY = re.compile(r"problem|question|latex|statement|prompt|alcumus", re.I)
_ID_KEY = re.compile(r"^(problem_?id|pid|id)$", re.I)
_CHOICE_KEY = re.compile(r"choice|option", re.I)
_TOPIC_KEY = re.compile(r"^(topic|subject|category|skill|focus)(_?name)?$", re.I)
_ANSWER_KEY = re.compile(r"answer_?(form|type|kind)|input_?type", re.I)
_MATHY = re.compile(r"\\\(|\\\[|\$|\\frac|\\dfrac|\\text|\\left|<p>")

# AoPS renders every equation as an image carrying its own LaTeX in `alt`.
_LATEX_IMG = re.compile(r"""<img\b[^>]*?\balt=(?:"([^"]*)"|'([^']*)')[^>]*>""", re.I)

# Selectors ordered most- to least-specific; the first two are the real ones.
_DOM_SELECTORS = (
    ".alc-problem-text",
    ".alc-current-problem",
    ".alc-problem-panel",
    "[class*='problem-text']",
    "[class*='problem']",
)

# Reads the statement out of the page bootstrap, and resolves the subject and
# topic ids against the lookup tables that ship alongside it.
_BOOTSTRAP_JS = """() => {
    const aops = window.AoPS || {};
    const bd = aops.bootstrap_data || aops.bd || {};
    const init = bd.alc_init_data;
    const user = init && init.user;
    const problem = user && user.current_problem;
    if (!problem) return null;

    const asList = v => Array.isArray(v) ? v : Object.values(v || {});
    const num = v => (v === null || v === undefined || v === '') ? null : Number(v);
    const levelData = (problem.level_data || [])[0] || {};

    // The subject IS carried on the problem, via level_data.subject_id.
    const subject = asList(user.subjects).find(
        s => String(s.subject_id) === String(levelData.subject_id)) || null;

    // The topic is NOT. Alcumus serves from the focus topic when one is set,
    // so this is an inference and is labelled as one.
    const focus = user.focus || {};
    const topic = asList(user.topics).find(
        t => String(t.topic_id) === String(focus.topic_id)) || null;

    const stats = o => ({
        num_correct: num(o.num_correct), num_incorrect: num(o.num_incorrect),
        num_giveup: num(o.num_giveup),
    });

    return {
        problem,
        subject: subject && {
            id: String(subject.subject_id), name: subject.name, alias: subject.alias,
            level: num(subject.level), xp: num(subject.xp),
        },
        subject_stats: subject && stats(subject),
        topic: topic && {
            id: String(topic.topic_id), name: topic.name, status: topic.status,
            progress: topic.progress,
        },
        topic_stats: topic && stats(topic),
        topic_source: topic ? 'focus' : null,
        level: num(levelData.level),
        xp: num(levelData.xp),
    };
}"""


@dataclass
class Capture:
    """One JSON response observed while the Alcumus page loaded."""

    url: str
    method: str
    status: int
    post_data: str | None
    data: Any

    def summary(self) -> dict[str, Any]:
        return {
            "score": score(self.data),
            "method": self.method,
            "url": self.url,
            "status": self.status,
            "post_data": self.post_data,
            "top_level_keys": list(self.data)[:20] if isinstance(self.data, dict) else None,
        }


def html_to_latex(markup: str) -> str:
    """Flatten AoPS markup to text, restoring math from `<img class=latex alt>`."""
    restored = _LATEX_IMG.sub(lambda m: m.group(1) or m.group(2) or "", markup)
    text = re.sub(r"<br\s*/?>", "\n", restored, flags=re.I)
    text = re.sub(r"</(p|div|li)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def walk(node: Any, path: str = "") -> Iterator[tuple[str, str, Any]]:
    """Yield (path, key, value) for every node in a JSON tree."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else str(key)
            yield here, str(key), value
            yield from walk(value, here)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            here = f"{path}[{index}]"
            yield here, "", value
            yield from walk(value, here)


def score(data: Any) -> int:
    """How much an arbitrary payload looks like an Alcumus problem."""
    total = 0
    longest = 0
    for _path, key, value in walk(data):
        if isinstance(value, str):
            if _TEXT_KEY.search(key) and len(value) > 20:
                total += 5
                longest = max(longest, len(value))
            elif len(value) > 20 and _MATHY.search(value):
                total += 2
        elif key and _HINT_KEY.search(key):
            total += 1
    if longest > 40:
        total += 3
    return total


def _choice_text(item: Any) -> str | None:
    if isinstance(item, (str, int, float)):
        return str(item)
    if isinstance(item, dict):
        for key in ("text", "label", "value", "choice", "html"):
            if isinstance(item.get(key), (str, int, float)):
                return str(item[key])
    return None


def extract(data: Any, endpoint: str | None = None) -> Problem:
    """Pull a Problem out of an arbitrary JSON payload, by key shape alone.

    Used for the bootstrap object and for any JSON XHR; deliberately tolerant so
    a renamed field degrades the result instead of breaking the fetch.
    """
    best_text = ""
    problem_id: str | None = None
    topic: str | None = None
    answer_kind: str | None = None
    choices: list[str] = []

    for _path, key, value in walk(data):
        if isinstance(value, str) and _TEXT_KEY.search(key) and len(value) > len(best_text):
            best_text = value
        elif problem_id is None and _ID_KEY.search(key) and isinstance(value, (str, int)):
            problem_id = str(value)
        elif topic is None and _TOPIC_KEY.search(key) and isinstance(value, str) and value:
            topic = value
        elif answer_kind is None and _ANSWER_KEY.search(key) and isinstance(value, str):
            answer_kind = value
        elif not choices and _CHOICE_KEY.search(key) and isinstance(value, list):
            found = [_choice_text(item) for item in value]
            if found and all(item is not None for item in found):
                choices = [html_to_latex(item) for item in found if item]

    return Problem(
        id=problem_id,
        text=html_to_latex(best_text),
        html=best_text if "<" in best_text else None,
        choices=choices,
        answer_kind=answer_kind,
        topic=topic,
        source="network",
        endpoint=endpoint,
        raw=data,
    )


def _answer_kind(problem: dict[str, Any]) -> str | None:
    """Alcumus signals the expected answer format with a few booleans."""
    if problem.get("is_interval"):
        return "interval notation"
    if problem.get("is_ulist"):
        return "unordered list"
    if problem.get("matrix_size"):
        return f"matrix ({problem['matrix_size']})"
    return None


def _from_bootstrap(page: Page) -> Problem | None:
    """Primary path: the statement AoPS embeds in the page itself."""
    try:
        payload = page.evaluate(_BOOTSTRAP_JS)
    except PlaywrightError:
        return None
    if not payload or not isinstance(payload.get("problem"), dict):
        return None

    problem = payload["problem"]
    markup = problem.get("problem_text") or ""
    # bbcode is the authored LaTeX; problem_text is the same thing rendered to
    # HTML with the math baked into <img> tags.
    text = (problem.get("problem_text_bbcode") or "").strip() or html_to_latex(markup)
    if not text:
        return None

    subject = payload.get("subject") or {}
    topic = payload.get("topic") or {}

    return Problem(
        id=str(problem["problem_id"]) if problem.get("problem_id") else None,
        text=text,
        html=markup or None,
        answer_kind=_answer_kind(problem),
        subject=subject.get("name"),
        topic=topic.get("name"),
        topic_source=payload.get("topic_source"),
        level=payload.get("level"),
        xp=payload.get("xp"),
        subject_stats={**subject, **(payload.get("subject_stats") or {})} or None,
        topic_stats={**topic, **(payload.get("topic_stats") or {})} or None,
        is_review=bool(problem.get("is_review")),
        seen_before=bool(problem.get("seen_before")),
        solved_before=bool(problem.get("solved_before")),
        source="bootstrap",
        endpoint=PROBLEM_URL,
        raw=problem,
    )


def _from_dom(page: Page) -> Problem | None:
    """Last resort: read the rendered node, restoring math from image alts."""
    for selector in _DOM_SELECTORS:
        target = page.locator(selector).first
        try:
            if target.count() == 0:
                continue
            markup = target.inner_html(timeout=2_000)
        except PlaywrightError:
            continue
        text = html_to_latex(markup)
        if len(text) >= 40:
            return Problem(text=text, html=markup, source="dom", endpoint=page.url)
    return None


def _record(response: Response, captures: list[Capture]) -> None:
    try:
        url = response.url
        if "artofproblemsolving.com" not in url or _ASSET.search(url):
            return
        if "json" not in (response.headers.get("content-type") or "").lower():
            return
        data = response.json()
        captures.append(
            Capture(
                url=url,
                method=response.request.method,
                status=response.status,
                post_data=response.request.post_data,
                data=data,
            )
        )
    except (PlaywrightError, ValueError):
        # Body already discarded, or not really JSON — nothing to salvage.
        return


def _best(captures: list[Capture]) -> Capture | None:
    ranked = sorted(captures, key=lambda capture: score(capture.data), reverse=True)
    if ranked and score(ranked[0].data) >= PROBLEM_SCORE:
        return ranked[0]
    return None


def _open_problem_page(context: BrowserContext, timeout_s: int) -> tuple[Page, list[Capture]]:
    """Load the page and wait for a structured source to appear."""
    page = context.new_page()
    captures: list[Capture] = []
    page.on("response", lambda response: _record(response, captures))

    page.goto(PROBLEM_URL, wait_until="domcontentloaded")
    if is_challenge(page):
        raise CloudflareChallenge(
            "Cloudflare is challenging this browser.\n"
            "Retry with --headed and solve it once; the cleared session is saved."
        )

    # The bootstrap ships with the document, so this almost always exits at once.
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _from_bootstrap(page) is not None or _best(captures) is not None:
            break
        page.wait_for_timeout(400)
    return page, captures


def fetch_current_problem(*, headed: bool = False, timeout_s: int = 30) -> Problem:
    """Return the problem Alcumus is currently showing your account."""
    with browser_context(headed=headed) as context:
        page, captures = _open_problem_page(context, timeout_s)

        problem = _from_bootstrap(page)
        if problem is not None:
            return problem

        best = _best(captures)
        if best is not None:
            return extract(best.data, best.url)

        from_dom = _from_dom(page)
        if from_dom is not None:
            return from_dom

        capture_log().write_text(
            json.dumps([capture.summary() for capture in captures], indent=2), encoding="utf-8"
        )
        if looks_logged_out(page):
            raise NotLoggedIn("Session expired. Run: python -m alcumus login")
        raise RuntimeError(
            "No problem found in the page bootstrap, any JSON response, or the DOM.\n"
            f"Saw {len(captures)} JSON response(s); summaries written to {capture_log()}.\n"
            "Run `python -m alcumus discover --headed` to see what the page does."
        )


def discover(*, headed: bool = False, timeout_s: int = 30) -> list[Capture]:
    """Every JSON XHR the Alcumus page makes, ranked by problem-likeness."""
    with browser_context(headed=headed) as context:
        _page, captures = _open_problem_page(context, timeout_s)
        return sorted(captures, key=lambda capture: score(capture.data), reverse=True)
