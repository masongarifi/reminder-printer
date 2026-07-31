"""Isolated Epson USB printer access."""
from __future__ import annotations

from filelock import FileLock, Timeout

import config


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

                device.set(align="center", bold=True, width=2, height=2)
                device.text(title + "\n\n")

                device.set(align="center", bold=False, width=1, height=1)
                device.text(date_line + "\n\n")
                device.set(align="left", bold=False, width=1, height=1)
                device.text(divider + "\n\n")

                if item_lines:
                    device.set(align="left", bold=False, width=2, height=2)
                    device.text(item_lines + "\n")

                # Explicitly restore normal text before the footer, feed, and cut.
                device.set(align="left", bold=False, width=1, height=1)
                device.text("\n" + item_count + "\n")
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
