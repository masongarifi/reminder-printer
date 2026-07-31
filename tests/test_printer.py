import sys
import types

import config
import printer


class FakeUsb:
    instances = []

    def __init__(self, *args, **kwargs):
        self.events = []
        FakeUsb.instances.append(self)

    def set(self, **kwargs):
        self.events.append(("set", kwargs))

    def text(self, value):
        self.events.append(("text", value))

    def _raw(self, value):
        self.events.append(("raw", value))

    def cut(self):
        self.events.append(("cut",))

    def close(self):
        self.events.append(("close",))


def test_native_double_size_alignment_and_reset_before_cut(monkeypatch, tmp_path):
    escpos = types.ModuleType("escpos")
    escpos_printer = types.ModuleType("escpos.printer")
    escpos_printer.Usb = FakeUsb
    monkeypatch.setitem(sys.modules, "escpos", escpos)
    monkeypatch.setitem(sys.modules, "escpos.printer", escpos_printer)
    monkeypatch.setattr(config, "USB_VENDOR_ID", 0x04B8)
    monkeypatch.setattr(config, "USB_PRODUCT_ID", 0x1234)
    monkeypatch.setattr(config, "PRINT_LOCK_FILE", str(tmp_path / "printer.lock"))
    monkeypatch.setattr(config, "FEED_LINES", 3)

    receipt = (
        "GROCERY LIST\n\nThu Jul 30, 2026\n\n----------\n\n"
        "[ ] Milk\n[ ] Bread\n\n2 ITEMS"
    )
    printer.print_receipt(receipt)
    events = FakeUsb.instances[-1].events

    title_text_index = events.index(("text", "GROCERY LIST\n\n"))
    assert events[title_text_index - 1] == ("raw", b"\x1d\x21\x11")

    date_text_index = events.index(("text", "Thu Jul 30, 2026\n\n"))
    assert events[date_text_index - 2] == (
        "set",
        {"align": "center", "bold": False},
    )
    assert events[date_text_index - 1] == ("raw", b"\x1d\x21\x01")
    assert events[date_text_index + 1] == ("raw", b"\x1d\x21\x00")

    reminder_text_index = events.index(("text", "[ ] Milk\n[ ] Bread\n"))
    assert events[reminder_text_index - 1] == ("raw", b"\x1d\x21\x11")
    assert events[reminder_text_index + 1] == ("raw", b"\x1d\x21\x00")

    count_text_index = events.index(("text", "\n2 ITEMS\n"))
    assert events[count_text_index - 2] == (
        "set",
        {"align": "center", "bold": False},
    )
    assert events[count_text_index - 1] == ("raw", b"\x1d\x21\x01")
    assert events[count_text_index + 1] == ("raw", b"\x1d\x21\x00")

    cut_index = events.index(("cut",))
    assert events[cut_index - 1] == ("text", "\n" * 3)
    assert events[cut_index - 2] == ("raw", b"\x1d\x21\x00")
    assert events[-1] == ("close",)
