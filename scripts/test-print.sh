#!/usr/bin/env bash
set -Eeuo pipefail
PORT="${REMINDER_PRINTER_PORT:-5055}"
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  -d '{"title":"Test Reminders","items":[{"text":"Confirm printer connection","completed":false},{"text":"Confirm text wrapping","completed":false},{"text":"Confirm automatic cutter","completed":false}]}' \
  "http://127.0.0.1:${PORT}/api/print-reminders"
echo

