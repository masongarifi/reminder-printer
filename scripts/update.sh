#!/usr/bin/env bash
set -Eeuo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$REPO_DIR/app.py" && "$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null)" == *"masongarifi/reminder-printer"* ]] ||
  { echo "Error: this is not the reminder-printer repository." >&2; exit 1; }
SUDO=""; [[ "$(id -u)" -eq 0 ]] || SUDO="sudo"
git -C "$REPO_DIR" pull --ff-only
"$REPO_DIR/.venv/bin/pip" install -r "$REPO_DIR/requirements.txt"
$SUDO systemctl daemon-reload
$SUDO systemctl restart reminder-printer.service
$SUDO systemctl is-active reminder-printer.service

