"""Browser session: sign in by hand once, reuse the session headlessly after."""

from __future__ import annotations

import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from playwright.sync_api import BrowserContext, Error as PlaywrightError, Page, sync_playwright

from .config import (
    BASE_URL,
    LOGIN_URL,
    PROBLEM_URL,
    USER_AGENT,
    capture_log,
    state_file,
)


class NotLoggedIn(RuntimeError):
    """No saved session, or the saved one has expired."""


class CloudflareChallenge(RuntimeError):
    """AoPS served an interstitial instead of the app."""


# Cookie names AoPS has used for the logged-in session, current first: the
# post-migration platform issues `platsessionid`, older pages used `aops*`.
# Matched as substrings so a rename doesn't break detection.
SESSION_COOKIE_HINTS = ("platsessionid", "aopssid", "aopsuid", "aops_sid", "aops_user_id")


def _launch(pw: Any, headed: bool):
    # Installed Chrome/Edge clears Cloudflare far more often than bundled Chromium.
    for channel in ("chrome", "msedge"):
        try:
            return pw.chromium.launch(headless=not headed, channel=channel)
        except PlaywrightError:
            continue
    return pw.chromium.launch(headless=not headed)


def _new_context(browser: Any, storage: Path | None) -> BrowserContext:
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1360, "height": 900},
        locale="en-US",
        storage_state=str(storage) if storage and storage.exists() else None,
    )
    context.set_default_timeout(45_000)
    return context


@contextmanager
def browser_context(headed: bool = False, require_state: bool = True) -> Iterator[BrowserContext]:
    """Yield a browser context carrying the saved AoPS session."""
    path = state_file()
    if require_state and not path.exists():
        raise NotLoggedIn(f"No saved session at {path}. Run: python -m alcumus login")

    with sync_playwright() as pw:
        browser = _launch(pw, headed)
        context = _new_context(browser, path)
        try:
            yield context
        finally:
            context.close()
            browser.close()


def save_state(context: BrowserContext) -> Path:
    path = state_file()
    context.storage_state(path=str(path))
    return path


def has_session_cookie(context: BrowserContext) -> bool:
    for cookie in context.cookies(BASE_URL):
        name = str(cookie.get("name", "")).lower()
        if cookie.get("value") and any(hint in name for hint in SESSION_COOKIE_HINTS):
            return True
    return False


def is_challenge(page: Page) -> bool:
    try:
        title = (page.title() or "").lower()
    except PlaywrightError:
        return False
    if "just a moment" in title or "attention required" in title:
        return True
    return page.locator("#challenge-running, #cf-challenge-running").count() > 0


def looks_logged_out(page: Page) -> bool:
    if "/login" in page.url:
        return True
    return page.locator('input[name="username"], input#username').count() > 0


def probe_logged_in(context: BrowserContext) -> bool:
    """Load the Alcumus page in a throwaway tab and report whether we're in."""
    page = context.new_page()
    try:
        page.goto(PROBLEM_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        if is_challenge(page):
            raise CloudflareChallenge(
                "Cloudflare is challenging this browser. Retry with --headed and solve it once."
            )
        return not looks_logged_out(page)
    finally:
        page.close()


def login(timeout_s: int = 300) -> Path:
    """Open a real browser window, wait for a human login, persist the session."""
    with sync_playwright() as pw:
        browser = _launch(pw, headed=True)
        context = _new_context(browser, state_file())
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        print("A browser window is open — sign in to Art of Problem Solving there.")
        print("Detecting the session automatically (Ctrl+C to abort)...")

        deadline = time.time() + timeout_s
        try:
            while time.time() < deadline:
                if has_session_cookie(context) and "/login" not in page.url:
                    if probe_logged_in(context):
                        path = save_state(context)
                        print(f"Signed in. Session saved to {path}")
                        return path
                page.wait_for_timeout(1500)
        finally:
            context.close()
            browser.close()

    raise TimeoutError(f"No login detected within {timeout_s}s.")


def logout() -> list[Path]:
    """Forget the saved session and any debug output."""
    removed: list[Path] = []
    for path in (state_file(), capture_log()):
        if path.exists():
            path.unlink()
            removed.append(path)
    return removed


def status(check: bool = False) -> dict[str, Any]:
    path = state_file()
    info: dict[str, Any] = {
        "session_file": str(path),
        "saved": path.exists(),
    }
    if path.exists():
        saved_at = datetime.fromtimestamp(path.stat().st_mtime)
        info["saved_at"] = saved_at.isoformat(timespec="seconds")
    if check and path.exists():
        with browser_context() as context:
            info["logged_in"] = probe_logged_in(context)
    return info
