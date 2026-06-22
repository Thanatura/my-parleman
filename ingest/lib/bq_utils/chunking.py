from collections.abc import Iterable, Iterator

from lib.bq_utils.models import BigQueryRow


def iter_chunked_rows(
    rows_iter: Iterable[BigQueryRow],
    chunk_size: int,
) -> Iterator[list[BigQueryRow]]:
    chunk: list[BigQueryRow] = []
    for row in rows_iter:
        chunk.append(row)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
