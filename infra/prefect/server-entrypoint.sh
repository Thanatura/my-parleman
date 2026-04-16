#!/bin/bash
set -e

. /opt/prefect/server-entrypoint.lib.sh

wait_for_database

SERVER_PORT="${PORT:-${PREFECT_SERVER_PORT:-8080}}"

exec prefect server start --host 0.0.0.0 --port "${SERVER_PORT}"