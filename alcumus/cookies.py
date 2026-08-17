"""Turn a cookie copied out of your browser into a saved session.

Accepts either form without being told which:
  * the `Cookie:` request header from DevTools -> Network -> any request
  * a JSON export from a cookie-editor extension

Input is read from a file, an environment variable, or stdin — never a command
line argument, which would land in your shell history.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from .config import state_file

COOKIE_DOMAIN = ".artofproblemsolving.com"

# Browser exports spell sameSite half a dozen ways; Playwright accepts three.
_SAME_SITE = {
    "lax": "Lax",
    "strict": "Strict",
    "none": "None",
    "no_restriction": "None",
    "unspecified": "Lax",
    "": "Lax",
}


class CookieError(ValueError):
    """The pasted cookie could not be understood."""


def _cookie(name: str, value: str, **overrides: Any) -> dict[str, Any]:
    cookie: dict[str, Any] = {
        "name": name,
        "value": value,
        "domain": COOKIE_DOMAIN,
        "path": "/",
        "expires": -1,  # session cookie
        "httpOnly": False,
        "secure": True,
        "sameSite": "Lax",
    }
    cookie.update({key: value for key, value in overrides.items() if value is not None})
    return cookie


def _from_header(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    if raw.lower().startswith("cookie:"):
        raw = raw.split(":", 1)[1]

    cookies: list[dict[str, Any]] = []
    for part in raw.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        if name.strip():
            cookies.append(_cookie(name.strip(), value.strip()))
    return cookies


def _from_json(data: Any) -> list[dict[str, Any]]:
    items = data.get("cookies") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise CookieError('JSON must be a list of cookies, or {"cookies": [...]}')

    cookies: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        expires = item.get("expires", item.get("expirationDate"))
        cookies.append(
            _cookie(
                str(item["name"]),
                str(item.get("value", "")),
                domain=item.get("domain") or COOKIE_DOMAIN,
                path=item.get("path") or "/",
                expires=float(expires) if isinstance(expires, (int, float)) else -1,
                httpOnly=bool(item.get("httpOnly", False)),
                secure=bool(item.get("secure", True)),
                sameSite=_SAME_SITE.get(str(item.get("sameSite", "")).lower(), "Lax"),
            )
        )
    return cookies


def parse(raw: str) -> list[dict[str, Any]]:
    """Parse either supported cookie format into Playwright cookie dicts."""
    raw = raw.strip()
    if not raw:
        raise CookieError("input was empty")
    if raw[0] in "[{":
        try:
            return _from_json(json.loads(raw))
        except json.JSONDecodeError as error:
            raise CookieError(f"looks like JSON but will not parse: {error}") from error
    return _from_header(raw)


def read_source(*, file: str | None, env: str | None, use_stdin: bool) -> str:
    if file:
        try:
            return Path(file).read_text(encoding="utf-8")
        except OSError as error:
            raise CookieError(f"cannot read {file}: {error}") from error
    if use_stdin:
        return sys.stdin.read()
    if env:
        value = os.environ.get(env)
        if not value:
            raise CookieError(f"environment variable {env} is unset or empty")
        return value
    raise CookieError("pick one of --file, --env, or --stdin")


def save(cookies: list[dict[str, Any]]) -> Path:
    """Write the cookies as a Playwright storage state, owner-readable only."""
    if not cookies:
        raise CookieError("no cookies found in the input")
    path = state_file()
    path.write_text(
        json.dumps({"cookies": cookies, "origins": []}, indent=2), encoding="utf-8"
    )
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # best effort; Windows ACLs are not POSIX modes
    return path
