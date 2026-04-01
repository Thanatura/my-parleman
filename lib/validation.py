"""Business validation rules for parsed data before load."""

from collections.abc import Sequence

from lib.bq_schemas import SCHEMA
from lib.models import BigQueryRow


class ValidationError(ValueError):
    """Raised when parsed rows violate load-time constraints."""


def validate_rows_for_table(table_name: str, rows: Sequence[BigQueryRow]) -> None:
    schema = SCHEMA[table_name]
    required_fields = [field.name for field in schema if field.mode == "REQUIRED"]

    for idx, row in enumerate(rows):
        payload = row.to_bq_dict()
        for field_name in required_fields:
            value = payload.get(field_name)
            if value is None or value == "":
                raise ValidationError(
                    f"{table_name}: row #{idx} missing required field '{field_name}'"
                )


def validate_all_tables(
    *,
    acteurs: Sequence[BigQueryRow],
    adresses: Sequence[BigQueryRow],
    mandats: Sequence[BigQueryRow],
    organes: Sequence[BigQueryRow],
    deports: Sequence[BigQueryRow],
) -> None:
    validate_rows_for_table("acteurs", acteurs)
    validate_rows_for_table("adresses", adresses)
    validate_rows_for_table("mandats", mandats)
    validate_rows_for_table("organes", organes)
    validate_rows_for_table("deports", deports)
