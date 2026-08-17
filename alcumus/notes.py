"""Write problems into an organised markdown vault (Obsidian, Foam, Logseq …).

Layout — folders keep browsing sane, wikilinks give the graph its edges:

    Alcumus.md                              hub
    Subjects/Algebra.md                     subject dashboard
    Topics/Graphing Multiple Lines.md       topic dashboard
    Problems/Algebra/Alcumus 30255.md       the problem itself

Problem notes are yours once created — re-saving never touches them. Subject and
topic notes are dashboards, so their frontmatter stats are refreshed on each
save while anything you write in the body is preserved.

Body text is plain with `$…$` math: no HTML, no image tags.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from .config import PROBLEM_URL
from .models import Problem

INDEX_NOTE = "Alcumus"
PROBLEMS_DIR = "Problems"
SUBJECTS_DIR = "Subjects"
TOPICS_DIR = "Topics"

WIKI_SEARCH = "https://artofproblemsolving.com/wiki/index.php?search={}"

EXPLANATION_PLACEHOLDER = (
    "*Not written yet — ask Claude to explain this topic, and it lands here.*"
)

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
# A colon only opens a mapping when followed by whitespace, so ISO timestamps and
# `https://` URLs are safe bare — and staying bare keeps Dataview's date typing.
_NEEDS_QUOTE = re.compile(r"""^\s|\s$|^[-?:,\[\]{}#&*!|>'"%@`]|:\s|\s#|[\[\]{},]|:$""")
_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)


@dataclass
class Saved:
    """Where a save landed."""

    problem: Path
    wrote_problem: bool
    subject: Path | None = None
    topic: Path | None = None
    index: Path | None = None
    current: Path | None = None
    # Set when the fetched problem differs from the one previously pointed at —
    # i.e. Alcumus has moved on since the last save.
    previous_problem_id: str | None = None


def safe_name(text: str, fallback: str = "Unknown") -> str:
    return _UNSAFE.sub("-", text).strip(" .") or fallback


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def note_name(problem: Problem) -> str:
    """Stable, filesystem-safe note title — one note per problem id."""
    stem = f"Alcumus {problem.id}" if problem.id else "Alcumus problem"
    return safe_name(stem, "Alcumus problem")


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if not text or _NEEDS_QUOTE.search(text):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def _frontmatter(pairs: list[tuple[str, Any]], tags: list[str]) -> str:
    lines = ["---"]
    lines += [f"{key}: {_yaml_scalar(value)}" for key, value in pairs if value is not None]
    lines.append(f"tags: [{', '.join(dict.fromkeys(tags))}]")
    lines += ["---", ""]
    return "\n".join(lines)


def _accuracy(stats: dict[str, Any]) -> str | None:
    """Share of attempts answered correctly, counting give-ups as misses."""
    counts = [stats.get(key) or 0 for key in ("num_correct", "num_incorrect", "num_giveup")]
    attempts = sum(counts)
    return f"{round(100 * counts[0] / attempts)}%" if attempts else None


def _upsert(path: Path, front: str, default_body: str) -> tuple[Path, bool]:
    """Create the note, or refresh only its frontmatter and keep the body."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(front + default_body, encoding="utf-8")
        return path, True

    existing = path.read_text(encoding="utf-8")
    body = _FRONTMATTER.sub("", existing, count=1)
    path.write_text(front + body, encoding="utf-8")
    return path, False


def to_markdown(problem: Problem, *, fetched_at: datetime | None = None) -> str:
    """Render the problem as a note."""
    stamp = (fetched_at or datetime.now()).isoformat(timespec="seconds")

    front = _frontmatter(
        [
            ("source", "alcumus"),
            ("type", "problem"),
            ("problem_id", problem.id),
            ("subject", problem.subject),
            ("topic", problem.topic),
            ("topic_source", problem.topic_source),
            ("level", problem.level),
            ("xp", problem.xp),
            ("answer_kind", problem.answer_kind),
            # Yours to update as you work: unsolved -> solved / missed.
            ("status", "unsolved"),
            ("review", problem.is_review),
            ("seen_before", problem.seen_before),
            ("solved_before", problem.solved_before),
            ("fetched", stamp),
            ("url", PROBLEM_URL),
        ],
        ["alcumus", "problem"]
        + [slug(name) for name in (problem.subject, problem.topic) if name],
    )

    # Leading "" puts the blank line after the frontmatter into the *body*.
    # Putting it in the frontmatter block instead would add one more blank line
    # on every dashboard refresh, since _upsert re-prepends the block each time.
    lines = ["", f"# {note_name(problem)}", "", problem.text, ""]

    if problem.choices:
        lines += ["## Choices", ""] + [f"- {choice}" for choice in problem.choices] + [""]

    links = [f"[[{safe_name(name)}]]" for name in (problem.topic, problem.subject) if name]
    links.append(f"[[{INDEX_NOTE}]]")

    # `Working` is appended to a step at a time while you solve; `Answer` is what
    # you finally type into Alcumus.
    lines += ["## Working", "", "", "## Answer", "", "", "## References", ""]
    lines.append("- " + " · ".join(links))
    if problem.topic:
        query = quote_plus(problem.topic)
        lines.append(f"- [AoPS Wiki: {problem.topic}]({WIKI_SEARCH.format(query)})")
    lines.append("")
    return front + "\n".join(lines)


def subject_markdown(problem: Problem, *, fetched_at: datetime | None = None) -> str:
    stats = problem.subject_stats or {}
    stamp = (fetched_at or datetime.now()).isoformat(timespec="seconds")
    front = _frontmatter(
        [
            ("source", "alcumus"),
            ("type", "subject"),
            ("subject_id", stats.get("id")),
            ("level", stats.get("level")),
            ("xp", stats.get("xp")),
            ("correct", stats.get("num_correct")),
            ("incorrect", stats.get("num_incorrect")),
            ("gave_up", stats.get("num_giveup")),
            ("accuracy", _accuracy(stats)),
            ("updated", stamp),
        ],
        ["alcumus", "subject", slug(problem.subject or "")],
    )
    body = (
        f"\n# {safe_name(problem.subject or '')}\n\n"
        f"Subject in [[{INDEX_NOTE}]].\n\n"
        f"## Explanation\n\n{EXPLANATION_PLACEHOLDER}\n\n"
        "## Notes\n\n"
    )
    return front + body


def topic_markdown(problem: Problem, *, fetched_at: datetime | None = None) -> str:
    stats = problem.topic_stats or {}
    stamp = (fetched_at or datetime.now()).isoformat(timespec="seconds")
    progress = stats.get("progress")
    front = _frontmatter(
        [
            ("source", "alcumus"),
            ("type", "topic"),
            ("topic_id", stats.get("id")),
            ("subject", problem.subject),
            ("status", stats.get("status")),
            ("progress", round(progress, 1) if isinstance(progress, (int, float)) else None),
            ("correct", stats.get("num_correct")),
            ("incorrect", stats.get("num_incorrect")),
            ("gave_up", stats.get("num_giveup")),
            ("accuracy", _accuracy(stats)),
            ("updated", stamp),
        ],
        ["alcumus", "topic", slug(problem.topic or "")],
    )

    name = safe_name(problem.topic or "")
    parents = [f"[[{safe_name(problem.subject)}]]"] if problem.subject else []
    parents.append(f"[[{INDEX_NOTE}]]")

    # The explanation is the point of a topic note — a link sends you elsewhere,
    # this keeps the method in the vault. Written once, then never overwritten:
    # _upsert refreshes frontmatter stats only.
    lines = [
        "",
        f"# {name}",
        "",
        "Topic in " + " · ".join(parents),
        "",
        "## Explanation",
        "",
        EXPLANATION_PLACEHOLDER,
        "",
        "## Notes",
        "",
        "",
    ]
    return front + "\n".join(lines)


INDEX_BODY = """---
source: alcumus
type: index
tags: [alcumus, index]
---

# Alcumus

Hub for problems fetched from
[Alcumus](https://artofproblemsolving.com/alcumus/problem).

Subjects and topics link back here, so this is the centre of the graph.
Written by `python -m alcumus save`.
"""


def ensure_index(vault: Path) -> tuple[Path, bool]:
    """Create the hub note, if it isn't there yet.

    Without it `[[Alcumus]]` resolves to an empty placeholder in the graph view.
    """
    path = vault / f"{INDEX_NOTE}.md"
    if path.exists():
        return path, False
    vault.mkdir(parents=True, exist_ok=True)
    path.write_text(INDEX_BODY, encoding="utf-8")
    return path, True


CURRENT_NOTE = "Current"
_FRONT_LINE = re.compile(r"^([a-z_]+):\s*(.*)$")


def read_current(vault: Path) -> dict[str, str] | None:
    """What the last fetch recorded as current — instant, no network.

    This is a *cache*. It says what Alcumus was serving when `save` last ran, not
    necessarily what it is serving now; re-run `save` to be sure.
    """
    path = vault / f"{CURRENT_NOTE}.md"
    if not path.exists():
        return None

    front: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = _FRONT_LINE.match(line)
        if match:
            front[match.group(1)] = match.group(2).strip().strip('"')
    return front or None


def write_current(vault: Path, problem: Problem, problem_note: Path, stamp: str) -> Path:
    """Point at the problem just fetched. Overwritten every save, by design."""
    try:
        relative = problem_note.relative_to(vault).as_posix()
    except ValueError:
        relative = problem_note.as_posix()

    front = _frontmatter(
        [
            ("source", "alcumus"),
            ("type", "current"),
            ("problem_id", problem.id),
            ("subject", problem.subject),
            ("topic", problem.topic),
            ("level", problem.level),
            ("problem_note", relative),
            ("fetched", stamp),
        ],
        ["alcumus", "current"],
    )

    facts = " · ".join(
        str(part)
        for part in (problem.subject, problem.topic, f"level {problem.level}" if problem.level else None)
        if part
    )
    body = (
        f"\n# Current problem\n\n[[{note_name(problem)}]]\n\n{facts}\n\n"
        "*Rewritten by `python -m alcumus save`. This reflects the last fetch —\n"
        "re-run `save` to confirm Alcumus is still serving it.*\n"
    )
    path = vault / f"{CURRENT_NOTE}.md"
    vault.mkdir(parents=True, exist_ok=True)
    path.write_text(front + body, encoding="utf-8")
    return path


def has_explanation(topic_note: Path | None) -> bool:
    """Whether a topic note's explanation has actually been written yet."""
    if topic_note is None or not topic_note.exists():
        return False
    body = topic_note.read_text(encoding="utf-8")
    return "## Explanation" in body and EXPLANATION_PLACEHOLDER not in body


def save_note(
    problem: Problem,
    vault: Path,
    *,
    overwrite: bool = False,
    fetched_at: datetime | None = None,
) -> Saved:
    """Write the problem, refresh its dashboards, and update the current pointer."""
    stamp = (fetched_at or datetime.now()).isoformat(timespec="seconds")
    was = read_current(vault) or {}
    previous = was.get("problem_id")

    index, _ = ensure_index(vault)

    subject_path = topic_path = None
    if problem.subject:
        subject_path, _ = _upsert(
            vault / SUBJECTS_DIR / f"{safe_name(problem.subject)}.md",
            *_split_front(subject_markdown(problem, fetched_at=fetched_at)),
        )
    if problem.topic:
        topic_path, _ = _upsert(
            vault / TOPICS_DIR / f"{safe_name(problem.topic)}.md",
            *_split_front(topic_markdown(problem, fetched_at=fetched_at)),
        )

    folder = vault / PROBLEMS_DIR / safe_name(problem.subject or "Unsorted")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{note_name(problem)}.md"

    wrote = overwrite or not path.exists()
    if wrote:
        path.write_text(to_markdown(problem, fetched_at=fetched_at), encoding="utf-8")

    current = write_current(vault, problem, path, stamp)

    return Saved(
        problem=path,
        wrote_problem=wrote,
        subject=subject_path,
        topic=topic_path,
        index=index,
        current=current,
        previous_problem_id=previous if previous and previous != problem.id else None,
    )


def _split_front(note: str) -> tuple[str, str]:
    """Split a rendered note into (frontmatter block, body)."""
    match = _FRONTMATTER.match(note)
    return (match.group(0), note[match.end() :]) if match else ("", note)
