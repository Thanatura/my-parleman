#!/bin/bash

wait_for_database() {
  DB_WAIT_TIMEOUT_SECONDS="${DB_WAIT_TIMEOUT_SECONDS:-300}"
  DB_WAIT_INTERVAL_SECONDS="${DB_WAIT_INTERVAL_SECONDS:-3}"

  DB_URL="${PREFECT_API_DATABASE_CONNECTION_URL:-}"

  if [ -z "${DB_URL}" ]; then
    echo "PREFECT_API_DATABASE_CONNECTION_URL not set, skipping DB readiness check"
    return 0
  fi

  DB_HOST_PORT=$(python3 /opt/prefect/scripts/db_url_host_port.py)

  DB_HOST="${DB_HOST_PORT%:*}"
  DB_PORT="${DB_HOST_PORT##*:}"

  echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} (timeout: ${DB_WAIT_TIMEOUT_SECONDS}s)"

  ELAPSED=0
  while true; do
    if python3 /opt/prefect/scripts/check_tcp.py --host "${DB_HOST}" --port "${DB_PORT}" --timeout 2
    then
      echo "PostgreSQL is reachable"
      break
    fi

    if [ "${ELAPSED}" -ge "${DB_WAIT_TIMEOUT_SECONDS}" ]; then
      echo "Timed out waiting for PostgreSQL after ${DB_WAIT_TIMEOUT_SECONDS}s"
      return 1
    fi

    sleep "${DB_WAIT_INTERVAL_SECONDS}"
    ELAPSED=$((ELAPSED + DB_WAIT_INTERVAL_SECONDS))
  done
}
