#!/usr/bin/env bash
set -Eeuo pipefail

[[ "$(uname -s)" == "Linux" ]] || { echo "Error: this installer must run on Linux." >&2; exit 1; }
command -v python3 >/dev/null || { echo "Error: Python 3 is required." >&2; exit 1; }
command -v systemctl >/dev/null || { echo "Error: systemd is required." >&2; exit 1; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$REPO_DIR/app.py" && -f "$REPO_DIR/systemd/reminder-printer.service" ]] ||
  { echo "Error: run scripts/install.sh from the reminder-printer repository." >&2; exit 1; }
SERVICE_USER="${REMINDER_PRINTER_USER:-${SUDO_USER:-$(id -un)}}"
id "$SERVICE_USER" >/dev/null 2>&1 || { echo "Error: Linux user '$SERVICE_USER' does not exist." >&2; exit 1; }
SUDO=""
[[ "$(id -u)" -eq 0 ]] || SUDO="sudo"

python3 -m venv "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/python" -m pip install --upgrade pip
"$REPO_DIR/.venv/bin/pip" install -r "$REPO_DIR/requirements.txt"

if [[ ! -f /etc/reminder-printer.env ]]; then
  $SUDO install -m 0644 "$REPO_DIR/.env.example" /etc/reminder-printer.env
  echo "Created /etc/reminder-printer.env. Set the Epson USB IDs there."
fi
sed -e "s|__SERVICE_USER__|$SERVICE_USER|g" -e "s|__REPOSITORY_PATH__|$REPO_DIR|g" \
  "$REPO_DIR/systemd/reminder-printer.service" |
  $SUDO tee /etc/systemd/system/reminder-printer.service >/dev/null
$SUDO systemctl daemon-reload
$SUDO systemctl enable reminder-printer.service
$SUDO systemctl restart reminder-printer.service
$SUDO systemctl --no-pager --full status reminder-printer.service || true

HOSTNAME_LOCAL="$(hostname).local"
PORT="$(grep -E '^REMINDER_PRINTER_PORT=' /etc/reminder-printer.env 2>/dev/null | cut -d= -f2 || true)"
echo "Reminder Printer URL: http://${HOSTNAME_LOCAL}:${PORT:-5055}/"
echo "If printing reports permission denied, see README.md 'USB permissions'."

