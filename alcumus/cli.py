"""Command line entry point: python -m alcumus <command>"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import client, config, cookies, notes, session
from .cookies import CookieError
from .session import CloudflareChallenge, NotLoggedIn


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alcumus",
        description="Read the problem Alcumus is currently showing your AoPS account.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="open a browser, sign in by hand, save the session")
    login.add_argument("--timeout", type=int, default=300, help="seconds to wait (default: 300)")

    paste = sub.add_parser(
        "import-cookies",
        help="save a cookie copied from your browser instead of logging in",
        description=(
            "Reads a `Cookie:` header string or a cookie-editor JSON export. "
            "Input never comes from an argument, so it stays out of shell history."
        ),
    )
    source = paste.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", metavar="PATH", help="file holding the cookie")
    source.add_argument(
        "--env",
        nargs="?",
        const="ALCUMUS_COOKIE",
        metavar="VAR",
        help="environment variable holding it (default: ALCUMUS_COOKIE)",
    )
    source.add_argument("--stdin", action="store_true", help="read it from stdin")
    paste.add_argument("--no-verify", action="store_true", help="skip the live session check")

    problem = sub.add_parser("problem", help="print the current problem")
    problem.add_argument("--json", action="store_true", help="print the parsed problem as JSON")
    problem.add_argument("--raw", action="store_true", help="print the untouched AoPS payload")
    problem.add_argument("--md", action="store_true", help="print it as an Obsidian note")
    problem.add_argument("--headed", action="store_true", help="show the browser window")
    problem.add_argument("--timeout", type=int, default=30)

    store = sub.add_parser("save", help="write the current problem into a markdown vault")
    store.add_argument(
        "--vault",
        type=Path,
        default=config.default_vault(),
        help="vault root (default: $ALCUMUS_VAULT, else ./vault)",
    )
    store.add_argument("--overwrite", action="store_true", help="replace an existing note")
    store.add_argument("--json", action="store_true", help="print the saved paths as JSON")
    store.add_argument("--headed", action="store_true")
    store.add_argument("--timeout", type=int, default=30)

    now = sub.add_parser(
        "current",
        help="which problem the last fetch recorded (no network)",
        description=(
            "Reads the vault's Current.md pointer. This is a cache of the last "
            "fetch — run `save` to confirm Alcumus is still serving it."
        ),
    )
    now.add_argument("--vault", type=Path, default=config.default_vault())
    now.add_argument("--json", action="store_true")

    found = sub.add_parser("discover", help="dump every JSON XHR the Alcumus page makes")
    found.add_argument("--headed", action="store_true")
    found.add_argument("--timeout", type=int, default=30)
    found.add_argument("--full", action="store_true", help="include each full payload")

    state = sub.add_parser("status", help="show whether a session is saved")
    state.add_argument("--check", action="store_true", help="also verify it against the live site")

    sub.add_parser("logout", help="delete the saved session and cached endpoint")
    return parser


def _import_cookies(args: argparse.Namespace) -> int:
    """Save a browser cookie as the session, then check it against the live site."""
    raw = cookies.read_source(file=args.file, env=args.env, use_stdin=args.stdin)
    parsed = cookies.parse(raw)
    path = cookies.save(parsed)

    names = [cookie["name"] for cookie in parsed]
    print(f"Saved {len(names)} cookie(s) to {path}")
    print(f"  names: {', '.join(names)}")  # names only — values stay unprinted

    if not any(
        hint in name.lower() for name in names for hint in session.SESSION_COOKIE_HINTS
    ):
        print(
            "  warning: none of these look like an AoPS session cookie "
            f"({', '.join(session.SESSION_COOKIE_HINTS)}) — copy the whole Cookie header",
            file=sys.stderr,
        )

    if args.no_verify:
        return 0

    with session.browser_context() as context:
        if session.probe_logged_in(context):
            print("Verified: the site accepts this session.")
            return 0
    print("The site does not accept this session — the cookie may be partial or expired.",
          file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        if args.command == "login":
            session.login(timeout_s=args.timeout)

        elif args.command == "import-cookies":
            return _import_cookies(args)

        elif args.command == "problem":
            problem = client.fetch_current_problem(
                headed=args.headed, timeout_s=args.timeout
            )
            if args.raw:
                print(json.dumps(problem.raw, indent=2, ensure_ascii=False))
            elif args.json:
                print(json.dumps(problem.to_dict(), indent=2, ensure_ascii=False))
            elif args.md:
                print(notes.to_markdown(problem))
            else:
                print(problem.pretty())

        elif args.command == "save":
            problem = client.fetch_current_problem(
                headed=args.headed, timeout_s=args.timeout
            )
            saved = notes.save_note(problem, args.vault, overwrite=args.overwrite)
            if args.json:
                print(
                    json.dumps(
                        {
                            "problem_id": problem.id,
                            "subject": problem.subject,
                            "topic": problem.topic,
                            "topic_source": problem.topic_source,
                            "level": problem.level,
                            "answer_kind": problem.answer_kind,
                            "problem_note": str(saved.problem),
                            "subject_note": str(saved.subject) if saved.subject else None,
                            "topic_note": str(saved.topic) if saved.topic else None,
                            "wrote_problem": saved.wrote_problem,
                            "topic_explained": notes.has_explanation(saved.topic),
                            "current_note": str(saved.current) if saved.current else None,
                            "previous_problem_id": saved.previous_problem_id,
                        },
                        indent=2,
                    )
                )
            else:
                verb = "wrote" if saved.wrote_problem else "kept (already exists)"
                print(f"{verb}: {saved.problem}")
                if not saved.wrote_problem:
                    print("  (pass --overwrite to replace it)")
                for label, path in (("subject", saved.subject), ("topic", saved.topic)):
                    if path:
                        print(f"  {label}: {path}")
                if saved.previous_problem_id:
                    print(f"  note: Alcumus moved on from problem {saved.previous_problem_id}")

        elif args.command == "current":
            pointer = notes.read_current(args.vault)
            if pointer is None:
                print(f"No current problem recorded in {args.vault}.", file=sys.stderr)
                print("Run: python -m alcumus save", file=sys.stderr)
                return 1
            if args.json:
                print(json.dumps(pointer, indent=2))
            else:
                for key in ("problem_id", "subject", "topic", "level", "problem_note", "fetched"):
                    if pointer.get(key):
                        print(f"{key + ':':14}{pointer[key]}")
                print("\n(cached from the last fetch — run `save` to confirm)")

        elif args.command == "discover":
            captures = client.discover(headed=args.headed, timeout_s=args.timeout)
            if not captures:
                print("No JSON responses captured.", file=sys.stderr)
                return 1
            for capture in captures:
                record = capture.summary()
                if args.full:
                    record["data"] = capture.data
                print(json.dumps(record, indent=2, ensure_ascii=False))

        elif args.command == "status":
            print(json.dumps(session.status(check=args.check), indent=2))

        elif args.command == "logout":
            removed = session.logout()
            print("\n".join(f"removed {path}" for path in removed) or "nothing to remove")

    except CookieError as error:
        print(f"Bad cookie input: {error}", file=sys.stderr)
        return 2
    except NotLoggedIn as error:
        print(f"Not signed in: {error}", file=sys.stderr)
        return 2
    except CloudflareChallenge as error:
        print(f"Blocked: {error}", file=sys.stderr)
        return 3
    except (TimeoutError, RuntimeError) as error:
        print(f"Failed: {error}", file=sys.stderr)
        return 1

    return 0
