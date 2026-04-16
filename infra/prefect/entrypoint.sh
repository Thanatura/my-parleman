#!/bin/bash
set -e

/**
 * This script is the entrypoint for the Prefect server container. 
 * It checks if the PREFECT_API_URL environment variable is set. 
 * If it is not set, it retrieves an access token from the Google Cloud metadata server,
 * and uses it to get the service URL for the Prefect API. 
 * Finally, it starts the Prefect server.
 */

if [ -z "$PREFECT_API_URL" ]; then
  TOKEN=$(curl -sf -H "Metadata-Flavor: Google" \
    http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

  SERVICE_URL=$(curl -sf \
    -H "Authorization: Bearer $TOKEN" \
    "https://run.googleapis.com/v2/projects/${GCP_PROJECT}/locations/europe-west1/services/${K_SERVICE}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['urls'][0])")

  export PREFECT_API_URL="${SERVICE_URL}/api"
fi

echo "PREFECT_API_URL=${PREFECT_API_URL}"

exec prefect server start --host 0.0.0.0 --port ${PREFECT_SERVER_PORT}