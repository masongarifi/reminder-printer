from datetime import datetime

import pytest

from formatter import Reminder, format_receipt, parse_json, parse_plain_text

NOW = datetime(2026, 7, 30)


def receipt(items, **kwargs):
    return format_receipt("Grocery List", items, now=NOW, **kwargs)


def test_empty_input():
    title, items = parse_plain_text("", "")
    assert title == "Reminders"
    assert items == []
    assert "0 ITEMS" in receipt(items)


def test_one_reminder_singular():
    assert "1 ITEM" in receipt([Reminder("Milk")])


def test_multiple_reminders_plural():
    assert "2 ITEMS" in receipt([Reminder("Milk"), Reminder("Bread")])


def test_long_reminder_wraps_and_indents():
    output = receipt([Reminder("A longer reminder that wraps cleanly")], width=20)
    item_lines = output.split("\n\n", 4)[3].splitlines()
    assert item_lines[0].startswith("[ ] ")
    assert all(line.startswith("    ") for line in item_lines[1:])


def test_completed_included():
    assert "[X] Done" in receipt([Reminder("Done", True)], include_completed=True)


def test_completed_excluded():
    assert "[X]" not in receipt([Reminder("Done", True)])
    assert "0 ITEMS" in receipt([Reminder("Done", True)])


def test_plain_text_bullets_preserve_internal_hyphens():
    _, items = parse_plain_text("- Buy sugar-free gum\n• Milk", "List")
    assert [i.text for i in items] == ["Buy sugar-free gum", "Milk"]


def test_plain_text_checkboxes():
    _, items = parse_plain_text("[ ] Open\n[x] Closed\n☑ Finished", "List")
    assert [(i.text, i.completed) for i in items] == [
        ("Open", False), ("Closed", True), ("Finished", True)
    ]


def test_json_input():
    title, items, included = parse_json({
        "title": "List", "include_completed": False,
        "items": [{"text": "Milk", "completed": False}]
    })
    assert title == "List" and items == [Reminder("Milk")] and included is False


def test_very_long_individual_word():
    output = receipt([Reminder("supercalifragilisticexpialidocious")], width=16)
    assert all(len(line) <= 16 for line in output.splitlines())


@pytest.mark.parametrize("width", [16, 42, 60])
def test_receipt_widths(width):
    output = receipt([Reminder("Some reminder text")], width=width)
    assert all(len(line) <= width for line in output.splitlines())


def test_title_longer_than_width():
    output = format_receipt("This title is much longer than width", [], width=16, now=NOW)
    assert all(len(line) <= 16 for line in output.splitlines())


def test_title_uses_no_alignment_padding_and_has_blank_line_after_it():
    output = receipt([Reminder("Milk")])
    assert output.startswith("GROCERY LIST\n\nThu Jul 30, 2026")


def test_double_width_items_wrap_at_half_receipt_width():
    output = receipt([Reminder("A reminder that needs wrapping")], width=42)
    item_section = output.split("\n\n", 4)[3]
    assert all(len(line) <= 21 for line in item_section.splitlines())
