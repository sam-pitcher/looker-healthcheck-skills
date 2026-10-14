#!/usr/bin/env bash
# run_bq_query.sh — Safe runner for BigQuery diagnostic queries.
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 "<SQL_QUERY>" [LOCATION]" >&2
  exit 1
fi

SQL="$1"
LOCATION="${2:-${BIGQUERY_LOCATION:-US}}"

exec bq query \
  --use_legacy_sql=false \
  --location="$LOCATION" \
  --format=prettyjson \
  --max_rows=100 \
  "$SQL"
