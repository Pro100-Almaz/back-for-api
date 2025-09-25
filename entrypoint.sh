#!/usr/bin/env sh
set -e

DB_HOST="${POSTGRES_HOST:-${DB_HOST:-}}"
DB_PORT="${POSTGRES_PORT:-${DB_PORT:-5432}}"

# Optional: wait for DB (uses DB_HOST/DB_PORT). Skips if DB_HOST is empty.
if [ -n "${DB_HOST:-}" ]; then
  echo "Waiting for DB at $DB_HOST:${DB_PORT} ..."
  i=0
  until python - <<'PY'
import os, socket, sys
host=os.getenv("DB_HOST","localhost")
port=int(os.getenv("DB_PORT","5432"))
s=socket.socket()
s.settimeout(1.0)
try:
    s.connect((host, port))
except Exception:
    sys.exit(1)
finally:
    s.close()
PY
  do
    i=$((i+1))
    if [ "$i" -ge "${DB_WAIT_RETRIES:-60}" ]; then
      echo "DB not reachable after $i tries" >&2
      exit 1
    fi
    sleep "${DB_WAIT_SLEEP:-1}"
  done
fi

# Optionally run collectstatic (default on). Set COLLECTSTATIC=0 to skip.
if [ "${COLLECTSTATIC:-1}" = "1" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# Optionally run makemigrations (default off—safer for prod)
if [ "${AUTO_MAKEMIGRATIONS:-0}" = "1" ]; then
  echo "Making migrations..."
  python manage.py makemigrations --noinput || true
fi

# Apply migrations (supports multiple DBs via MIGRATE_DATABASES="default reporting")
DBS="$(printf "%s" "${MIGRATE_DATABASES:-default}" | tr ',' ' ')"
for db in $DBS; do
  echo "Applying migrations on database: $db"
  python manage.py migrate --noinput --database "$db"
done

# Hand off to whatever CMD was provided (Gunicorn by default)
exec "$@"
