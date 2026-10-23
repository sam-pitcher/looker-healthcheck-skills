#!/usr/bin/env bash
# stream_lookml.sh — Fast parallel fetcher for LookML project files via looker-cli.
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <PROJECT_ID> [OUTPUT_DIR]" >&2
  exit 1
fi

PROJECT_ID="$1"
OUTPUT_DIR="${2:-/tmp/lookml_stream_${PROJECT_ID}}"
mkdir -p "$OUTPUT_DIR"

echo "⚡ Fetching file list for project '$PROJECT_ID'..."
FILES=$(looker-cli project file ls "$PROJECT_ID" --plain)

echo "⚡ Streaming LookML files in parallel..."
echo "$FILES" | grep -E "\.(model|explore|view)\.lkml$" | while read -r filepath; do
  [ -z "$filepath" ] && continue
  target_file="$OUTPUT_DIR/$filepath"
  mkdir -p "$(dirname "$target_file")"
  looker-cli project file cat "$PROJECT_ID" "$filepath" > "$target_file" &
done

wait
echo "✅ Streamed project files to: $OUTPUT_DIR"
