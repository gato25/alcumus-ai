"""Offline checks for cookie parsing — no browser, no network."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["ALCUMUS_AI_HOME"] = tempfile.mkdtemp(prefix="alcumus-test-")

from alcumus import cookies  # noqa: E402

HEADER = "Cookie: aopssid=abc123; aopsuid=456; other_flag=yes"
EDITOR_JSON = json.dumps(
    [
        {
            "name": "aopssid",
            "value": "abc123",
            "domain": ".artofproblemsolving.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "no_restriction",
            "expirationDate": 1893456000,
        }
    ]
)


def test_parses_header_form() -> None:
    parsed = cookies.parse(HEADER)
    assert [c["name"] for c in parsed] == ["aopssid", "aopsuid", "other_flag"]
    assert parsed[0]["value"] == "abc123"
    assert parsed[0]["domain"] == cookies.COOKIE_DOMAIN
    assert parsed[0]["expires"] == -1


def test_header_without_prefix_and_with_padding() -> None:
    assert [c["name"] for c in cookies.parse("  a=1 ;  b=2;  ")] == ["a", "b"]


def test_values_containing_equals_survive() -> None:
    (parsed,) = cookies.parse("token=abc==def")
    assert parsed["value"] == "abc==def"


def test_parses_editor_json() -> None:
    (parsed,) = cookies.parse(EDITOR_JSON)
    assert parsed["name"] == "aopssid"
    assert parsed["httpOnly"] is True
    assert parsed["sameSite"] == "None"  # mapped from no_restriction
    assert parsed["expires"] == 1893456000


def test_parses_storage_state_shape() -> None:
    wrapped = json.dumps({"cookies": json.loads(EDITOR_JSON)})
    assert [c["name"] for c in cookies.parse(wrapped)] == ["aopssid"]


def test_rejects_empty_and_broken_input() -> None:
    for bad in ("", "   ", "[not json"):
        try:
            cookies.parse(bad)
        except cookies.CookieError:
            continue
        raise AssertionError(f"should have rejected {bad!r}")


def test_save_writes_playwright_storage_state() -> None:
    path = cookies.save(cookies.parse(HEADER))
    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["origins"] == []
    assert {c["name"] for c in state["cookies"]} == {"aopssid", "aopsuid", "other_flag"}


def test_save_rejects_empty_cookie_list() -> None:
    try:
        cookies.save([])
    except cookies.CookieError:
        return
    raise AssertionError("should have rejected an empty cookie list")


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
