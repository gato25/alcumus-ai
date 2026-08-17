"""Offline checks for the markdown vault — no browser, no network."""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alcumus.models import Problem  # noqa: E402
from alcumus.notes import (  # noqa: E402
    EXPLANATION_PLACEHOLDER,
    has_explanation,
    note_name,
    read_current,
    save_note,
    subject_markdown,
    to_markdown,
    topic_markdown,
)

STAMP = datetime(2026, 8, 17, 21, 30, 0)
PROBLEM = Problem(
    id="30255",
    text=(
        "A line parallel to $3x-7y = 65$ passes through the point $(7,4)$ "
        "and $(0,K)$. What is the value of K?"
    ),
    html='A line parallel to <img class="latex" alt="$3x-7y = 65$"> ...',
    answer_kind="interval notation",
    subject="Algebra",
    topic="Graphing Multiple Lines",
    topic_source="focus",
    level=17,
    xp=99,
    subject_stats={"id": "2", "level": 9, "xp": 13266, "num_correct": 176,
                   "num_incorrect": 15, "num_giveup": 34},
    topic_stats={"id": "85", "status": "ready", "progress": 53.070713,
                 "num_correct": 7, "num_incorrect": 2, "num_giveup": 2},
)


def test_body_is_plain_latex_with_no_markup() -> None:
    note = to_markdown(PROBLEM, fetched_at=STAMP)
    body = note.split("---", 2)[2]
    assert "<img" not in body and "latex.artofproblemsolving" not in body
    assert PROBLEM.text in body


def test_frontmatter_carries_classification() -> None:
    front = to_markdown(PROBLEM, fetched_at=STAMP).split("---")[1]
    assert "problem_id: 30255" in front
    assert "subject: Algebra" in front
    assert "topic: Graphing Multiple Lines" in front
    assert "topic_source: focus" in front  # honest: inferred, not authoritative
    assert "level: 17" in front
    assert "answer_kind: interval notation" in front  # plain scalar: nothing special
    # Bare, not quoted: Dataview types these as a date and a link.
    assert "fetched: 2026-08-17T21:30:00" in front
    assert "url: https://artofproblemsolving.com/alcumus/problem" in front
    assert "tags: [alcumus, problem, algebra, graphing-multiple-lines]" in front


def test_yaml_special_values_get_quoted() -> None:
    note = to_markdown(Problem(id="1", text="x", subject="Ratios, Rates"), fetched_at=STAMP)
    assert 'subject: "Ratios, Rates"' in note  # comma would start a YAML flow sequence


def test_problem_links_up_the_hierarchy() -> None:
    note = to_markdown(PROBLEM, fetched_at=STAMP)
    for link in ("[[Graphing Multiple Lines]]", "[[Algebra]]", "[[Alcumus]]"):
        assert link in note
    assert "wiki/index.php?search=Graphing+Multiple+Lines" in note


def test_subject_and_topic_dashboards() -> None:
    subject = subject_markdown(PROBLEM, fetched_at=STAMP)
    assert "type: subject" in subject and "level: 9" in subject
    assert "accuracy: 78%" in subject  # 176 / (176+15+34)

    topic = topic_markdown(PROBLEM, fetched_at=STAMP)
    assert "type: topic" in topic and "status: ready" in topic
    assert "progress: 53.1" in topic
    assert "[[Algebra]]" in topic  # topic hangs off its subject in the graph
    assert "## Explanation" in topic  # the point of a topic note, not a link out


def test_problem_note_has_a_working_section() -> None:
    note = to_markdown(PROBLEM, fetched_at=STAMP)
    assert "## Working" in note and "## Answer" in note


def test_has_explanation_detects_the_placeholder() -> None:
    vault = Path(tempfile.mkdtemp(prefix="alcumus-explained-"))
    saved = save_note(PROBLEM, vault, fetched_at=STAMP)
    assert saved.topic is not None

    assert not has_explanation(saved.topic), "a fresh placeholder is not an explanation"
    assert not has_explanation(None)
    assert not has_explanation(vault / "Topics" / "Nonexistent.md")

    saved.topic.write_text(
        saved.topic.read_text(encoding="utf-8").replace(
            EXPLANATION_PLACEHOLDER, "Parallel lines have equal slopes."
        ),
        encoding="utf-8",
    )
    assert has_explanation(saved.topic)


def test_current_pointer_tracks_the_latest_fetch() -> None:
    vault = Path(tempfile.mkdtemp(prefix="alcumus-current-"))
    assert read_current(vault) is None, "nothing fetched yet"

    saved = save_note(PROBLEM, vault, fetched_at=STAMP)
    assert saved.current == vault / "Current.md"
    assert saved.previous_problem_id is None, "first fetch has no predecessor"

    pointer = read_current(vault)
    assert pointer is not None
    assert pointer["problem_id"] == "30255"
    assert pointer["topic"] == "Graphing Multiple Lines"
    assert pointer["problem_note"] == "Problems/Algebra/Alcumus 30255.md"
    assert f"[[{note_name(PROBLEM)}]]" in (vault / "Current.md").read_text(encoding="utf-8")


def test_moving_to_a_new_problem_is_reported() -> None:
    """So an abandoned half-solved note doesn't silently become an orphan."""
    vault = Path(tempfile.mkdtemp(prefix="alcumus-moved-"))
    save_note(PROBLEM, vault, fetched_at=STAMP)

    same = save_note(PROBLEM, vault, fetched_at=STAMP)
    assert same.previous_problem_id is None, "same problem is not a move"

    onward = save_note(
        Problem(id="30256", text="y", subject="Algebra"), vault, fetched_at=STAMP
    )
    assert onward.previous_problem_id == "30255"
    assert read_current(vault)["problem_id"] == "30256"


def test_problem_note_starts_unsolved() -> None:
    assert "status: unsolved" in to_markdown(PROBLEM, fetched_at=STAMP)


def test_note_name_is_filesystem_safe() -> None:
    assert note_name(PROBLEM) == "Alcumus 30255"
    assert note_name(Problem(id="a/b:c*d", text="x")) == "Alcumus a-b-c-d"
    assert note_name(Problem(text="x")) == "Alcumus problem"


def test_vault_layout() -> None:
    vault = Path(tempfile.mkdtemp(prefix="alcumus-layout-"))
    saved = save_note(PROBLEM, vault, fetched_at=STAMP)

    assert saved.problem == vault / "Problems" / "Algebra" / "Alcumus 30255.md"
    assert saved.subject == vault / "Subjects" / "Algebra.md"
    assert saved.topic == vault / "Topics" / "Graphing Multiple Lines.md"
    assert (vault / "Alcumus.md").exists()
    assert saved.wrote_problem


def test_unknown_subject_still_files_somewhere() -> None:
    vault = Path(tempfile.mkdtemp(prefix="alcumus-unsorted-"))
    saved = save_note(Problem(id="7", text="x"), vault, fetched_at=STAMP)
    assert saved.problem == vault / "Problems" / "Unsorted" / "Alcumus 7.md"
    assert saved.subject is None and saved.topic is None


def test_save_never_clobbers_your_problem_note() -> None:
    vault = Path(tempfile.mkdtemp(prefix="alcumus-vault-"))
    saved = save_note(PROBLEM, vault, fetched_at=STAMP)

    saved.problem.write_text("my own worked solution", encoding="utf-8")
    again = save_note(PROBLEM, vault, fetched_at=STAMP)
    assert not again.wrote_problem
    assert again.problem.read_text(encoding="utf-8") == "my own worked solution"

    assert save_note(PROBLEM, vault, overwrite=True, fetched_at=STAMP).wrote_problem


def test_dashboards_refresh_stats_but_keep_your_writing() -> None:
    vault = Path(tempfile.mkdtemp(prefix="alcumus-refresh-"))
    saved = save_note(PROBLEM, vault, fetched_at=STAMP)

    assert saved.topic is not None
    # A hand-written explanation is expensive to produce and must never be lost
    # to a routine stats refresh.
    written = saved.topic.read_text(encoding="utf-8").replace(
        EXPLANATION_PLACEHOLDER,
        "Perpendicular slopes are negative reciprocals: $m_1 m_2 = -1$.",
    )
    saved.topic.write_text(written + "\nI keep forgetting slope-intercept.\n", encoding="utf-8")

    moved_on = Problem(
        id="30256", text="y", subject="Algebra", topic="Graphing Multiple Lines",
        topic_stats={"id": "85", "status": "ready", "progress": 61.5,
                     "num_correct": 9, "num_incorrect": 2, "num_giveup": 2},
    )
    save_note(moved_on, vault, fetched_at=STAMP)

    refreshed = saved.topic.read_text(encoding="utf-8")
    assert "progress: 61.5" in refreshed, "stats should track your real progress"
    assert "I keep forgetting slope-intercept." in refreshed, "your writing must survive"
    assert "negative reciprocals" in refreshed, "the explanation must survive"

    # Refreshing must be idempotent. The blank line after the frontmatter lives
    # in the body precisely so it is not re-added on every pass; without that,
    # notes grow a blank line and a stacked `---` block per save.
    for _ in range(4):
        save_note(moved_on, vault, fetched_at=STAMP)
    settled = saved.topic.read_text(encoding="utf-8")
    assert settled == refreshed, "repeated refreshes must not drift the file"
    assert settled.count("---") == 2, "frontmatter must not stack up"


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
