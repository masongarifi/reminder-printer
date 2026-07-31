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

    assert events[0] == (
        "set",
        {"align": "center", "bold": True, "width": 2, "height": 2},
    )
    assert ("text", "GROCERY LIST\n\n") in events
    assert (
        "set",
        {"align": "left", "bold": False, "width": 2, "height": 2},
    ) in events
    cut_index = events.index(("cut",))
    assert events[cut_index - 1] == ("text", "\n" * 3)
    assert events[cut_index - 2] == ("text", "\n2 ITEMS\n")
    assert events[cut_index - 3] == (
        "set",
        {"align": "left", "bold": False, "width": 1, "height": 1},
    )
    assert events[-1] == ("close",)
