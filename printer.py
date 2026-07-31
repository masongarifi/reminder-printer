"""Isolated Epson USB printer access."""
from __future__ import annotations

from filelock import FileLock, Timeout

import config

DOUBLE_SIZE = b"\x1d\x21\x11"
MEDIUM_SIZE = b"\x1d\x21\x01"
NORMAL_SIZE = b"\x1d\x21\x00"


class PrinterError(RuntimeError):
    pass


def print_receipt(receipt: str) -> None:
    if not config.USB_VENDOR_ID or not config.USB_PRODUCT_ID:
        raise PrinterError(
            "USB vendor and product IDs are not configured. Set "
            "REMINDER_PRINTER_USB_VENDOR_ID and REMINDER_PRINTER_USB_PRODUCT_ID."
        )
    try:
        with FileLock(config.PRINT_LOCK_FILE, timeout=30):
            device = None
            try:
                from escpos.printer import Usb
                device = Usb(
                    config.USB_VENDOR_ID,
                    config.USB_PRODUCT_ID,
                    interface=config.USB_INTERFACE,
                    in_ep=config.USB_IN_EP,
                    out_ep=config.USB_OUT_EP,
                    timeout=0,
                )
                sections = receipt.split("\n\n", 4)
                if len(sections) != 5:
                    raise PrinterError("Receipt has an invalid internal format.")
                title, date_line, divider, item_lines, item_count = sections

                # Configure alignment/emphasis first because some printers or
                # python-escpos versions emit a size command from set().
                # GS ! is deliberately the final command before enlarged text.
                device.set(align="center", bold=True)
                device._raw(DOUBLE_SIZE)
                device.text(title + "\n\n")
                device._raw(NORMAL_SIZE)

                device.set(align="center", bold=False)
                device._raw(MEDIUM_SIZE)
                device.text(date_line + "\n\n")
                device._raw(NORMAL_SIZE)
                device.set(align="left", bold=False)
                device.text(divider + "\n\n")

                if item_lines:
                    # No formatting or initialization command may occur between
                    # this raw GS ! command and the reminder text.
                    device.set(align="left", bold=False)
                    device._raw(DOUBLE_SIZE)
                    device.text(item_lines + "\n")
                    device._raw(NORMAL_SIZE)

                device.set(align="center", bold=False)
                device._raw(MEDIUM_SIZE)
                device.text("\n" + item_count + "\n")
                # Keep subsequent jobs safe before feeding and cutting.
                device._raw(NORMAL_SIZE)
                if config.FEED_LINES:
                    device.text("\n" * config.FEED_LINES)
                device.cut()
            finally:
                if device is not None:
                    device.close()
    except Timeout as exc:
        raise PrinterError("Printer is busy; another print job holds the lock.") from exc
    except PrinterError:
        raise
    except Exception as exc:
        message = str(exc)
        hint = (
            " Check that the Epson printer is connected and that the service user "
            "has USB permission (udev rule or lp group)."
        )
        raise PrinterError(f"Unable to print: {message}.{hint}") from exc
