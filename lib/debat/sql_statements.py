from typing import TypeVar

from lib.debat.entities import CompteRendu, DebatParseResult, Intervention, PointSeance


MAX_QUERY_SIZE = 1_024_000  # 1 MB limit per query
T = TypeVar("T")


def _split_into_size_limited_batches(
    entities: list[T], max_size: int = MAX_QUERY_SIZE
) -> list[list[T]]:
    """Split entities into batches ensuring each batch's string representation stays under max_size."""
    batches: list[list[T]] = []
    current_batch: list[T] = []
    current_size = 0

    for entity in entities:
        entity_str = str(entity)
        entity_size = len(entity_str)

        # If adding this entity would exceed the limit, start a new batch
        if current_size + entity_size + 2 > max_size and current_batch:  # +2 for ", "
            batches.append(current_batch)
            current_batch = [entity]
            current_size = entity_size
        else:
            current_batch.append(entity)
            current_size += entity_size + 2

    if current_batch:
        batches.append(current_batch)

    return batches


def build_sql_statements(
    parsed_debats: DebatParseResult,
    gcp_project: str,
    bq_dataset: str,
) -> list[str]:
    statements: list[str] = [
        CompteRendu.create_table_sql_text(
            project_id=gcp_project, dataset_id=bq_dataset
        ),
        CompteRendu.truncate_table_sql_text(
            project_id=gcp_project, dataset_id=bq_dataset
        ),
    ]

    # Insert CompteRendus in size-limited batches
    for comptes_rendus in _split_into_size_limited_batches(
        parsed_debats.comptes_rendus
    ):
        insert_compte_rendus = f"""
        INSERT INTO {gcp_project}.{bq_dataset}.comptes_rendus{CompteRendu.columns()}
        VALUES {",".join(str(compte_rendu) for compte_rendu in comptes_rendus)};
        """
        statements.append(insert_compte_rendus)

    statements.append(
        PointSeance.create_table_sql_text(project_id=gcp_project, dataset_id=bq_dataset)
    )
    statements.append(
        PointSeance.truncate_table_sql_text(
            project_id=gcp_project, dataset_id=bq_dataset
        )
    )

    # Insert PointSeance in size-limited batches
    for points in _split_into_size_limited_batches(parsed_debats.points):
        insert_points = f"""
        INSERT INTO {gcp_project}.{bq_dataset}.points_seance{PointSeance.columns()}
        VALUES {",".join(str(point) for point in points)};
        """
        statements.append(insert_points)

    statements.append(
        Intervention.create_table_sql_text(
            project_id=gcp_project, dataset_id=bq_dataset
        )
    )
    statements.append(
        Intervention.truncate_table_sql_text(
            project_id=gcp_project, dataset_id=bq_dataset
        )
    )

    # Insert Interventions in size-limited batches
    for batch in _split_into_size_limited_batches(parsed_debats.interventions):
        insert_interventions = f"""
        INSERT INTO {gcp_project}.{bq_dataset}.interventions{Intervention.columns()}
        VALUES {",".join(str(intervention) for intervention in batch)};
        """
        statements.append(insert_interventions)

    return statements
