"""The shape of a fetched problem."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Problem:
    """One Alcumus problem, as currently served to your account.

    `text` is plain text with LaTeX left intact (Alcumus statements are LaTeX
    rendered by MathJax, so `$...$` and `\\(...\\)` survive on purpose).
    `raw` is the untouched JSON payload, so nothing the heuristics miss is lost.
    """

    id: str | None = None
    text: str = ""
    html: str | None = None
    choices: list[str] = field(default_factory=list)
    answer_kind: str | None = None
    subject: str | None = None
    topic: str | None = None
    # Alcumus puts no topic id on the problem itself; when a focus topic is set
    # it serves from that topic, so `topic` is an inference. This records it.
    topic_source: str | None = None
    level: int | None = None
    xp: int | None = None
    subject_stats: dict[str, Any] | None = None
    topic_stats: dict[str, Any] | None = None
    is_review: bool = False
    seen_before: bool = False
    solved_before: bool = False
    source: str = "bootstrap"
    endpoint: str | None = None
    raw: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def pretty(self) -> str:
        lines: list[str] = []
        if self.subject:
            lines.append(f"Subject: {self.subject}")
        if self.topic:
            suffix = " (inferred from focus)" if self.topic_source == "focus" else ""
            lines.append(f"Topic:   {self.topic}{suffix}")
        if self.id:
            lines.append(f"Problem: {self.id}")
        if self.level is not None:
            lines.append(f"Level:   {self.level}" + (f" · {self.xp} XP" if self.xp else ""))
        if self.answer_kind:
            lines.append(f"Answer:  {self.answer_kind}")
        flags = [
            name
            for name, on in (
                ("review", self.is_review),
                ("seen before", self.seen_before),
                ("solved before", self.solved_before),
            )
            if on
        ]
        if flags:
            lines.append(f"Flags:   {', '.join(flags)}")
        if lines:
            lines.append("")
        lines.append(self.text or "(no problem text found)")
        if self.choices:
            lines.append("")
            for i, choice in enumerate(self.choices):
                lines.append(f"  ({chr(ord('a') + i)}) {choice}")
        origin = self.endpoint or "?"
        lines += ["", f"[source: {self.source} · {origin}]"]
        return "\n".join(lines)
