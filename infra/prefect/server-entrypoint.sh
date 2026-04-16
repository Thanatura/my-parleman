#!/bin/bash
set -e

. /opt/prefect/server-entrypoint.lib.sh

resolve_prefect_api_url

echo "PREFECT_API_URL=${PREFECT_API_URL}"

wait_for_database

SERVER_PORT="${PORT:-${PREFECT_SERVER_PORT:-8080}}"

exec prefect server start --host 0.0.0.0 --port "${SERVER_PORT}"