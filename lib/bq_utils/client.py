from google.cloud import bigquery
from google.oauth2 import service_account

from lib.config import ProjectConfig


def create_bq_client(config: ProjectConfig) -> bigquery.Client:
    credentials = service_account.Credentials.from_service_account_info(
        config.service_account_info
    )
    return bigquery.Client(
        project=config.gcp_project,
        credentials=credentials,
    )
