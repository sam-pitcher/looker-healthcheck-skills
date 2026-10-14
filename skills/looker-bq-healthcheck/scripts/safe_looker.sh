#!/usr/bin/env bash
# safe_looker.sh — Enforces read-only safety guardrails for looker-cli commands.
set -euo pipefail

CMD="$*"

# Destructive keyword blacklist
FORBIDDEN_PATTERN="\\b(rm|delete|drop|truncate|destroy|wipeout|purge)\\b"

if echo "$CMD" | grep -Ei "$FORBIDDEN_PATTERN" > /dev/null; then
  echo "🚨 SAFETY GUARDRAIL TRIGGERED: Destructive command blocked!" >&2
  echo "Blocked pattern detected in: looker-cli $CMD" >&2
  exit 1
fi

exec looker-cli "$@"
