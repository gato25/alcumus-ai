# alcumus-ai

Fetches the problem [Alcumus](https://artofproblemsolving.com/alcumus/problem) is
currently showing **your** AoPS account, as clean LaTeX.

```
Problem: 30255

A line parallel to $3x-7y = 65$ passes through the point $(7,4)$ and $(0,K)$. What is the value of K?

[source: bootstrap · https://artofproblemsolving.com/alcumus/problem]
```

## Why it needs a browser

`artofproblemsolving.com` sits behind Cloudflare and returns `403` to
unauthenticated requests. The Alcumus XHR endpoint (`/m/alcumus/ajax.php`) is
real but also answers `403` to anything that isn't a genuine browser session.
So this drives a logged-in browser rather than talking to the API directly.

You authenticate **once**; later runs are headless and take a couple of seconds.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium   # only if you have no local Chrome/Edge
```

It prefers your installed Chrome, then Edge, then bundled Chromium — real Chrome
clears Cloudflare most reliably.

## Authenticate

Either sign in through a browser window:

```bash
python -m alcumus login
```

…or import the session from a browser you're already signed into. In DevTools →
Network, click any `artofproblemsolving.com` request and copy the whole
**`Cookie:`** request header (a cookie-editor JSON export works too):

```bash
python -m alcumus import-cookies --file cookie.txt              # from a file
$env:ALCUMUS_COOKIE = "..."; python -m alcumus import-cookies --env
Get-Content cookie.txt | python -m alcumus import-cookies --stdin
```

It prints cookie **names** only, warns if none look like an AoPS session cookie,
and verifies against the live site. There is deliberately no `--cookie <value>`
flag — that would put a live credential in your shell history.

Copy the entire header, not just one cookie. The current platform uses
`platsessionid`; a partial copy verifies as logged-out.

## Use

```bash
python -m alcumus problem
```

| Command | What it does |
| --- | --- |
| `python -m alcumus save` | write it into a markdown vault |
| `python -m alcumus current` | which problem the last fetch recorded (no network) |
| `python -m alcumus problem --md` | print the note without saving |
| `python -m alcumus problem --json` | parsed problem as JSON |
| `python -m alcumus problem --raw` | the untouched `current_problem` object |
| `python -m alcumus problem --headed` | watch the browser do it |
| `python -m alcumus discover --full` | every JSON XHR the page makes, ranked |
| `python -m alcumus status --check` | is the saved session still good? |
| `python -m alcumus logout` | forget the session |

As a library:

```python
from alcumus import fetch_current_problem

problem = fetch_current_problem()
print(problem.text)         # LaTeX source, ready to hand to a model
print(problem.id)           # "30255"
print(problem.answer_kind)  # "interval notation" / "unordered list" / None
print(problem.raw)          # full bootstrap object
```

## Practising with Claude Code

The point of the vault. In Claude Code:

```
/alcumus
```

That fetches the current problem, checks whether its topic has an explanation
(and writes one if not), shows you the problem — and then **waits for you**.

You drive, one step at a time, in your own words:

> **you:** convert it to slope-intercept form
> **claude:** $3x - 7y = 65 \Rightarrow y = \frac{3}{7}x - \frac{65}{7}$. Valid — that's the slope isolated.
> **you:** so the parallel line is $y = \frac{3}{7}x + b$

Each accepted step is appended to `## Working` in the problem note, so the note
becomes your worked page:

```markdown
## Working

1. Convert to slope-intercept → $y = \frac{3}{7}x - \frac{65}{7}$
2. Parallel line has the same slope → $y = \frac{3}{7}x + b$
3. ~~Multiply by $x$~~ — introduces an extraneous root
```

The rules the skill enforces on Claude:

- **never states the next step**, not even as a leading question
- **never does two steps at once**, however obvious the rest is
- wrong step → says *what rule it breaks*, not what to do instead
- valid-but-useless step → applies it anyway; dead ends teach
- hint → the smallest nudge that names the idea, never the move
- **never submits an answer to AoPS** — you type it in yourself

Say "just solve it" and it will, after checking once that you mean it.

## Reading the vault on your phone

The vault is published as a website by [Quartz](https://quartz.jzhao.xyz/),
living in [site/](site/):

```bash
cd site
npm ci --include=optional   # --include=optional matters, see below
npm run serve               # local preview with hot reload
npm run build               # one-off build into site/public
```

Pushing to `main` triggers [the deploy workflow](.github/workflows/deploy-vault.yml),
which builds and publishes to GitHub Pages. **One-time setup:** in the repo's
*Settings → Pages*, set **Source** to **GitHub Actions**.

You get working wikilinks, full-text search, the graph view, KaTeX math, and
your `<details>` collapsibles — in any mobile browser, nothing installed.

### Two traps worth knowing

**Quartz globs content with `gitignore: true`.** Anything ignored by git is
silently dropped from the published site — no error, just a missing page. So
Quartz builds straight from `vault/` (`quartz build -d ../vault`) rather than
copying into `site/content/`: a generated copy would have to be gitignored,
which would make Quartz see zero files.

**npm skips optional platform binaries.** A plain `npm ci` leaves out the native
builds `sharp` and `lightningcss` need, and the build dies on
`Cannot find module '../lightningcss.<platform>.node'`. Always
`--include=optional`.

`vault/index.md` is the site's landing page — Quartz serves `index.md` at the
root — and doubles as the vault's home note in Obsidian.

## Into a markdown vault

```bash
python -m alcumus save --vault "D:\notes"     # or set $ALCUMUS_VAULT
```

Folders keep browsing sane; wikilinks give the graph view its edges:

```
Alcumus.md                              hub
Current.md                              pointer at the problem last fetched
Subjects/Algebra.md                     subject dashboard — level, XP, accuracy
Topics/Graphing Multiple Lines.md       topic dashboard — status, progress
Problems/Algebra/Alcumus 30255.md       the problem
```

### Which problem is "current"?

Two answers, and the difference matters:

- **`save` is authoritative.** It asks AoPS directly, so it's right even if you
  answered a few problems in the browser since.
- **`Current.md` is a cache** of the last fetch — instant and offline
  (`python -m alcumus current`), but stale the moment you answer on the website.

Never infer the current problem from the newest file in the vault. When `save`
finds a different problem than the pointer held, it reports
`previous_problem_id`, so an abandoned half-solved note gets noticed instead of
quietly becoming an orphan.

Problem notes carry `status: unsolved`, which `/alcumus` updates to `solved` or
`missed` when you report back — that's what makes the vault queryable later.

Each problem links to its topic, each topic to its subject, each subject to the
hub — so the graph clusters by subject instead of forming one flat star.

The problem note is plain text and `$…$` math, no HTML and no image tags:

```markdown
---
source: alcumus
type: problem
problem_id: 30255
subject: Algebra
topic: Graphing Multiple Lines
topic_source: focus
level: 17
xp: 99
review: false
seen_before: false
solved_before: false
fetched: 2026-08-17T21:54:43
url: https://artofproblemsolving.com/alcumus/problem
tags: [alcumus, problem, algebra, graphing-multiple-lines]
---

# Alcumus 30255

A line parallel to $3x-7y = 65$ passes through the point $(7,4)$ and $(0,K)$. What is the value of K?

## My answer


## Solution


## References

- [[Graphing Multiple Lines]] · [[Algebra]] · [[Alcumus]]
- [AoPS Wiki: Graphing Multiple Lines](https://artofproblemsolving.com/wiki/index.php?search=Graphing+Multiple+Lines)
```

Obsidian renders `$…$` natively with MathJax. Frontmatter scalars are left bare
where YAML allows it, so Dataview types `fetched` as a date and `url` as a link.

### How the classification is derived

`subject` is **authoritative** — it comes from `level_data.subject_id` on the
problem. `topic` is **inferred**: Alcumus puts no topic id on the problem, so
this is the focus topic the problem was served from. That's why every note
records `topic_source: focus` rather than presenting it as fact. With no focus
set, `topic` is empty and the note files under `Problems/<Subject>/` anyway.

### What gets overwritten

| Note | On re-save |
| --- | --- |
| `Problems/…` | **never touched** — your worked answer is safe (`--overwrite` forces it) |
| `Subjects/…`, `Topics/…` | frontmatter stats refreshed, your body text preserved |
| `Alcumus.md` | created once, then left alone |

Dashboard refreshes are idempotent — repeated saves don't stack frontmatter
blocks or grow blank lines, and a test pins that.

### Topic and subject explanations

Every topic and subject note has an `## Explanation` written to a fixed
standard — 3Blue1Brown for the intuition, AoPS for the technique — in five
ascending levels, so the same note serves a beginner and someone prepping for an
olympiad:

| Level | What it does |
| --- | --- |
| **L1 · Intuition** | the mental picture; *derives* the rule instead of stating it |
| **L2 · Mechanics** | the method, the formulas, one fully worked example |
| **L3 · Fluency** | shortcuts that skip the long way, and why they're valid |
| **L4 · Competition** | AMC/AIME applications and standard tricks |
| **L5 · Deeper** | olympiad level: the general structure underneath |

Then a blunt **Where marks get lost** list.

The standard lives in
[.claude/skills/alcumus/references/explanation-standard.md](.claude/skills/alcumus/references/explanation-standard.md);
the `/alcumus` skill follows it whenever it meets a topic that isn't explained
yet. Subject notes are written as **maps** that link out to their topics rather
than duplicating them.

Because dashboard refreshes only touch frontmatter, an explanation is written
**once and never overwritten**. A test pins that: expensive hand-written content
must survive a routine stats refresh.

### AoPS solutions are not available up front

AoPS does **not** ship the worked solution in the page — it only appears after
you submit an answer. So `## Solution` on a problem note stays empty for you to
fill in. Getting the official text would mean submitting answers on your behalf,
which this tool does not do.

## How it finds the problem

Alcumus does **not** fetch the statement over XHR. AoPS embeds it in the page
bootstrap, and that is the primary source:

```
window.AoPS.bootstrap_data.alc_init_data.user.current_problem
```

`problem_text_bbcode` there is the authored LaTeX — no HTML, nothing to unpick.
The same object carries `problem_id`, `is_review`, `seen_before`,
`solved_before`, and the answer-format flags `is_interval` / `is_ulist` /
`matrix_size`.

Two fallbacks exist because AoPS moves things: any JSON response that scores as
a problem, then scraping the rendered node.

### The trap in scraping

AoPS renders every equation as an image with the LaTeX in its `alt`:

```html
A line parallel to <img class="latex" alt="$3x-7y = 65$"> passes through …
```

`innerText` drops `<img>`, so naive scraping returns
`"A line parallel to  passes through the point  and ."` — grammatical, plausible,
and missing all the math. `html_to_latex()` rebuilds the statement from the alt
attributes, and a test pins it.

## When it breaks

```bash
python -m alcumus discover --headed --full
```

That prints every JSON call with a score. Response summaries from a failed run
are written to `~/.alcumus-ai/last-capture.json`.

If `problem` reports `source: dom`, the bootstrap path broke and you're on the
lossy fallback — worth fixing rather than ignoring.

## Tests

```bash
python tests/test_extract.py
python tests/test_cookies.py
```

Offline: no browser, no network, no account needed.

## Storage

Session file and capture log live in `~/.alcumus-ai/` (override with
`ALCUMUS_AI_HOME`). Nothing stores your password — but `state.json` holds a live
session cookie, so treat it like one: it is outside the repo, chmod'd to
owner-only where the OS supports it, and `python -m alcumus logout` deletes it.
Cookies expire; re-import or re-login when `status --check` says you're out.

Intended for personal use with your own account — one fetch per run, no polling
loop.
