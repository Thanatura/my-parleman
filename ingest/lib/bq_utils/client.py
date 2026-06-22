from google.cloud import bigquery
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from prefect import get_run_logger

from lib.config import ProjectConfig
import urllib.request

def get_adc_service_account_email() -> str | None:
    try:
        credentials, _ = default()
    except DefaultCredentialsError:
        return None
    return getattr(credentials, "service_account_email", None)


def get_runtime_service_account_email() -> str | None:
    url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
    req = urllib.request.Request(url, headers={"Metadata-Flavor": "Google"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode("utf-8")


def create_bq_client(config: ProjectConfig) -> bigquery.Client:
    logger = get_run_logger()

    service_account_email = get_adc_service_account_email()
    runtime_service_account_email = get_runtime_service_account_email()
    logger.info(
        "BigQuery ADC service account email: %s",
        service_account_email or "(not found)",
    )
    logger.info(
        "BigQuery runtime service account email: %s",
        runtime_service_account_email or "(not found)",
    )
    client = bigquery.Client(project=config.gcp_project)

    return client
