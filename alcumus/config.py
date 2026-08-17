"""Shared URLs and on-disk paths."""

from __future__ import annotations

import os
from pathlib import Path

BASE_URL = "https://artofproblemsolving.com"
PROBLEM_URL = f"{BASE_URL}/alcumus/problem"
LOGIN_URL = f"{BASE_URL}/login"

# Headless Chromium's default user agent is a reliable way to get a Cloudflare
# interstitial instead of the app, so we always present as desktop Chrome.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def home() -> Path:
    """Directory holding the saved session and endpoint cache."""
    root = Path(os.environ.get("ALCUMUS_AI_HOME") or (Path.home() / ".alcumus-ai"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def state_file() -> Path:
    return home() / "state.json"


def default_vault() -> Path:
    """Markdown vault to write notes into (ALCUMUS_VAULT, else ./vault)."""
    return Path(os.environ.get("ALCUMUS_VAULT") or Path.cwd() / "vault")


def capture_log() -> Path:
    return home() / "last-capture.json"
