#!/usr/bin/env bash
# validate_lookml.sh — Validates LookML project compilation via looker-cli.
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <PROJECT_ID>" >&2
  exit 1
fi

PROJECT_ID="$1"
exec looker-cli project validate "$PROJECT_ID"
