"""Offline checks for the payload heuristics — no browser, no network.

These pin the part that has to survive AoPS changing its JSON shape: picking the
problem payload out of a pile of XHRs and pulling fields out of it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alcumus.client import PROBLEM_SCORE, extract, html_to_latex, score  # noqa: E402

# Exactly how AoPS ships math: an image whose alt attribute holds the LaTeX.
# innerText drops these, which silently deletes every equation.
AOPS_MARKUP = (
    "\n\t\t\tA line parallel to "
    '<img src="//latex.artofproblemsolving.com/1/c/a/1ca.png" class="latex" '
    'alt="$3x-7y = 65$" style="vertical-align: -3px" width="102" height="16"> '
    "passes through the point "
    '<img src="//latex.artofproblemsolving.com/f/0/7/f07.png" class="latex" alt="$(7,4)$"> '
    'and <span style="white-space:nowrap;">'
    '<img src="//latex.artofproblemsolving.com/6/a/4/6a4.png" class="latex" alt="$(0,K)$">.'
    "</span> What is the value of K?\n\t\t"
)

NESTED = {
    "response": {
        "problem_id": 3141592,
        "problem_text": (
            "What is the value of $\\frac{1}{2} + \\frac{1}{3}$? "
            "Express your answer as a common fraction."
        ),
        "category": "Fractions",
        "answer_form": "number",
    }
}

FLAT_HTML = {
    "problem": {
        "id": "abc123",
        "html": "<p>Compute <b>\\(7 \\times 8\\)</b>.</p><p>Show your work.</p>",
    }
}

MULTIPLE_CHOICE = {
    "problem_text": "Which of these is prime? Consider $n \\in \\{4, 9, 11, 15\\}$.",
    "choices": [{"text": "4"}, {"text": "9"}, {"text": "11"}, {"text": "15"}],
}

NOISE = [
    {"response": {"unread_messages": 0, "notifications": []}},
    {"success": True, "server_time": 1700000000},
    {"user": {"id": 88, "username": "someone", "avatar": "/img/a.png"}},
]


def test_problem_payloads_outscore_noise() -> None:
    for payload in (NESTED, FLAT_HTML, MULTIPLE_CHOICE):
        assert score(payload) >= PROBLEM_SCORE, payload
    for payload in NOISE:
        assert score(payload) < PROBLEM_SCORE, payload


def test_extracts_nested_fields() -> None:
    problem = extract(NESTED, "https://example.test/ajax.php")
    assert problem.id == "3141592"
    assert problem.topic == "Fractions"
    assert problem.answer_kind == "number"
    assert "\\frac{1}{2}" in problem.text  # LaTeX must survive
    assert problem.endpoint == "https://example.test/ajax.php"
    assert problem.raw is NESTED


def test_strips_html_but_keeps_math() -> None:
    problem = extract(FLAT_HTML)
    assert "<p>" not in problem.text
    assert "\\(7 \\times 8\\)" in problem.text
    assert problem.html is not None


def test_reads_multiple_choice() -> None:
    problem = extract(MULTIPLE_CHOICE)
    assert problem.choices == ["4", "9", "11", "15"]


def test_restores_math_from_image_alts() -> None:
    """The regression that made the first live fetch drop every equation."""
    text = html_to_latex(AOPS_MARKUP)
    assert text == (
        "A line parallel to $3x-7y = 65$ passes through the point $(7,4)$ "
        "and $(0,K)$. What is the value of K?"
    )


def test_bootstrap_shaped_payload_is_understood() -> None:
    """The real shape of user.current_problem, as seen on the live page."""
    payload = {
        "problem_id": "30255",
        "problem_text_bbcode": "A line parallel to $3x-7y = 65$ passes through $(0,K)$.",
        "problem_text": AOPS_MARKUP,
        "is_review": False,
        "is_interval": False,
        "is_ulist": False,
        "matrix_size": None,
    }
    assert score(payload) >= PROBLEM_SCORE
    problem = extract(payload)
    assert problem.id == "30255"
    assert "$3x-7y = 65$" in problem.text


def test_missing_fields_do_not_crash() -> None:
    problem = extract({"totally": ["un", "expected", 1, None]})
    assert problem.text == ""
    assert problem.choices == []


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
