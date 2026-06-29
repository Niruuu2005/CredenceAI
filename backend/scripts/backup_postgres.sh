#!/bin/sh
# Backup PostgreSQL database. Set DATABASE_URL or pass connection args.
set -e
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="${1:-./backup_credenceai_${TIMESTAMP}.sql}"

if [ -n "$DATABASE_URL" ]; then
  pg_dump "$DATABASE_URL" > "$OUTPUT"
else
  PGHOST="${PGHOST:-localhost}"
  PGUSER="${PGUSER:-user}"
  PGDATABASE="${PGDATABASE:-credenceai}"
  pg_dump -h "$PGHOST" -U "$PGUSER" "$PGDATABASE" > "$OUTPUT"
fi

echo "Backup written to $OUTPUT"
