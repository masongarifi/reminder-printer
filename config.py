"""Environment-based configuration for reminder-printer."""
import os


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value, 0)


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


HOST = os.getenv("REMINDER_PRINTER_HOST", "0.0.0.0")
PORT = _int("REMINDER_PRINTER_PORT", 5055)
RECEIPT_WIDTH = max(16, _int("REMINDER_PRINTER_WIDTH", 42))
USB_VENDOR_ID = _int("REMINDER_PRINTER_USB_VENDOR_ID", 0)
USB_PRODUCT_ID = _int("REMINDER_PRINTER_USB_PRODUCT_ID", 0)
INCLUDE_COMPLETED = _bool("REMINDER_PRINTER_INCLUDE_COMPLETED", False)
FEED_LINES = max(0, _int("REMINDER_PRINTER_FEED_LINES", 3))
USB_INTERFACE = _int("REMINDER_PRINTER_USB_INTERFACE", 0)
USB_IN_EP = _int("REMINDER_PRINTER_USB_IN_EP", 0x82)
USB_OUT_EP = _int("REMINDER_PRINTER_USB_OUT_EP", 0x01)
PRINT_LOCK_FILE = os.getenv(
    "REMINDER_PRINTER_LOCK_FILE", "/tmp/reminder-printer.lock"
)

