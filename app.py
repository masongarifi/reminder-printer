"""Flask application for reminder-printer."""
from __future__ import annotations

from flask import Flask, jsonify, render_template, request

import config
from formatter import format_receipt, parse_json, parse_plain_text
from printer import PrinterError, print_receipt

app = Flask(__name__)


def _request_data():
    if request.is_json:
        payload = request.get_json(silent=False)
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        title, items, include = parse_json(payload)
    else:
        title = request.args.get("title") or request.form.get("title")
        if request.form:
            text = request.form.get("text", "")
            raw_include = request.form.get("include_completed")
        else:
            text = request.get_data(as_text=True)
            raw_include = request.args.get("include_completed")
        title, items = parse_plain_text(text, title)
        include = (
            raw_include.lower() in {"1", "true", "yes", "on"}
            if raw_include is not None else None
        )
    include = config.INCLUDE_COMPLETED if include is None else include
    return title, items, include


def _formatted():
    title, items, include = _request_data()
    return format_receipt(
        title, items, width=config.RECEIPT_WIDTH, include_completed=include
    )


@app.get("/")
def index():
    return render_template("index.html", width=config.RECEIPT_WIDTH)


@app.get("/api/health")
def health():
    return jsonify(status="ok", service="reminder-printer")


@app.post("/api/preview-reminders")
def preview_reminders():
    try:
        receipt = _formatted()
        if request.accept_mimetypes.best == "text/plain":
            return receipt, 200, {"Content-Type": "text/plain; charset=utf-8"}
        return jsonify(ok=True, receipt=receipt)
    except (ValueError, TypeError) as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.post("/api/print-reminders")
def print_reminders():
    try:
        receipt = _formatted()
        print_receipt(receipt)
        return jsonify(ok=True, message="Reminder list printed successfully.")
    except (ValueError, TypeError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    except PrinterError as exc:
        app.logger.exception("Print failed")
        return jsonify(ok=False, error=str(exc)), 503


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT)

