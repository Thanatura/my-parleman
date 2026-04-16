#!/bin/bash

resolve_prefect_api_url() {
  if [ -n "${PREFECT_API_URL:-}" ]; then
    return 0
  fi

  TOKEN=$(curl -sf -H "Metadata-Flavor: Google" \
    http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

  SERVICE_URL=$(curl -sf \
    -H "Authorization: Bearer ${TOKEN}" \
    "https://run.googleapis.com/v2/projects/${GCP_PROJECT}/locations/europe-west1/services/${K_SERVICE}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['urls'][0])")

  export PREFECT_API_URL="${SERVICE_URL}/api"
}

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
