from collections.abc import Mapping, Sequence
from google.cloud import bigquery
from lib.config import ProjectConfig
from lib.bq_utils.models import BigQueryRow


def ensure_dataset(client: bigquery.Client, config: ProjectConfig) -> None:
    dataset_ref = bigquery.Dataset(f"{config.gcp_project}.{config.bq_dataset}")
    dataset_ref.location = "EU"
    client.create_dataset(dataset_ref, exists_ok=True)


class ValidationError(ValueError):
    pass


def validate_rows_for_table(
    table_name: str,
    schema: Mapping[str, list[bigquery.SchemaField]],
    rows: Sequence[BigQueryRow],
) -> None:
    schema_fields = schema[table_name]
    required_fields = [
        field.name for field in schema_fields if field.mode == "REQUIRED"
    ]

    for idx, row in enumerate(rows):
        payload = row.to_bq_dict()
        for field_name in required_fields:
            value = payload.get(field_name)
            if value is None or value == "":
                raise ValidationError(
                    f"{table_name}: row #{idx} missing required field '{field_name}'"
                )
