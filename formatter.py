"""Parse reminder inputs and produce printer-safe receipt text."""
from __future__ import annotations

import re
import textwrap
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable


@dataclass(frozen=True)
class Reminder:
    text: str
    completed: bool = False


_CHECKED = re.compile(
    r"^\s*(?:\[[xX]\]|[☑✅✔✓]|(?:completed|done)\s*[:\-])\s*",
    re.IGNORECASE,
)
_UNCHECKED = re.compile(r"^\s*(?:\[\s\]|[☐□])\s*")
_BULLET = re.compile(r"^\s*(?:[-*•·]\s+|\d+[.)]\s+)")


def ascii_safe(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    substitutions = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "…": "...", "\t": " ",
    }
    text = "".join(substitutions.get(ch, ch) for ch in text)
    return text.encode("ascii", "ignore").decode("ascii")


def clean_item(line: str) -> Reminder | None:
    line = line.replace("\t", " ").strip()
    if not line:
        return None
    completed = bool(_CHECKED.match(line))
    line = _CHECKED.sub("", line, count=1)
    line = _UNCHECKED.sub("", line, count=1)
    line = _BULLET.sub("", line, count=1)
    line = re.sub(r"\s+", " ", line).strip()
    return Reminder(ascii_safe(line), completed) if line else None


def parse_plain_text(text: str, title: str | None = None) -> tuple[str, list[Reminder]]:
    lines = [line for line in (text or "").splitlines() if line.strip()]
    resolved_title = (title or "").strip()
    if not resolved_title and lines:
        first = clean_item(lines[0])
        if first and not re.match(r"^\s*(?:\[[ xX]\]|[☐☑□✅✔✓•*·-])", lines[0]):
            resolved_title = first.text
            lines = lines[1:]
    items = [item for line in lines if (item := clean_item(line))]
    return ascii_safe(resolved_title or "Reminders"), items


def parse_json(payload: dict[str, Any]) -> tuple[str, list[Reminder], bool | None]:
    title = ascii_safe(payload.get("title") or "Reminders").strip() or "Reminders"
    raw_items = payload.get("items", [])
    if not isinstance(raw_items, list):
        raise ValueError("'items' must be a JSON array")
    items: list[Reminder] = []
    for entry in raw_items:
        if isinstance(entry, str):
            item = clean_item(entry)
        elif isinstance(entry, dict):
            text = re.sub(r"\s+", " ", ascii_safe(entry.get("text"))).strip()
            item = Reminder(text, bool(entry.get("completed", False))) if text else None
        else:
            raise ValueError("Each item must be a string or object")
        if item:
            items.append(item)
    included = payload.get("include_completed")
    if included is not None and not isinstance(included, bool):
        raise ValueError("'include_completed' must be true or false")
    return title, items, included


def _wrap_item(item: Reminder, width: int) -> list[str]:
    marker = "[X] " if item.completed else "[ ] "
    body_width = max(1, width - len(marker))
    wrapped = textwrap.wrap(
        item.text,
        width=body_width,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=True,
        drop_whitespace=True,
    ) or [""]
    return [marker + wrapped[0], *(" " * len(marker) + line for line in wrapped[1:])]


def format_receipt(
    title: str,
    items: Iterable[Reminder],
    *,
    width: int = 42,
    include_completed: bool = False,
    now: datetime | None = None,
) -> str:
    width = max(16, int(width))
    safe_title = ascii_safe(title).strip() or "Reminders"
    title_lines = textwrap.wrap(safe_title.upper(), width=width, break_long_words=True) or ["REMINDERS"]
    date_line = (now or datetime.now()).strftime("%a %b %d, %Y")
    selected = [item for item in items if include_completed or not item.completed]
    lines = [line.center(width).rstrip() for line in title_lines]
    lines += [date_line.center(width).rstrip(), "", "-" * width, ""]
    for item in selected:
        lines.extend(_wrap_item(item, width))
    count = len(selected)
    lines += ["", f"{count} {'ITEM' if count == 1 else 'ITEMS'}"]
    return "\n".join(lines)

