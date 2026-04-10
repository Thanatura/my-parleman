import io
import zipfile
from collections.abc import Iterator

import requests


def fetch_zip_file(url: str) -> bytes:
    response = requests.get(url, timeout=(5, 45))
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        # Preserve existing behavior (raise ValueError) but keep HTTP context.
        body_preview = response.text[:200] if hasattr(response, "text") else ""
        raise ValueError(
            f"Failed to fetch file from {url}, status code: {response.status_code}, "
            f"response body (truncated): {body_preview}"
        ) from exc
    return response.content


def extract_file_contents(archive_content: bytes) -> list[str]:
    file_contents = []
    with zipfile.ZipFile(io.BytesIO(archive_content)) as zip_archive:
        for file_info in zip_archive.infolist():
            if file_info.is_dir():
                continue
            with zip_archive.open(file_info) as file:
                file_content = file.read().decode("utf-8")
                file_contents.append(file_content)
    return file_contents


def extract_zip_contents_with_dossier(
    archive_content: bytes,
) -> Iterator[tuple[str, str]]:
    """Yield ``(dossier_id, json_content)`` tuples for each JSON file in a zip archive."""
    with zipfile.ZipFile(io.BytesIO(archive_content)) as zip_archive:
        for file_info in zip_archive.infolist():
            if file_info.is_dir() or not file_info.filename.endswith(".json"):
                continue

            parts = file_info.filename.strip("/").split("/")

            # Récupérer le dossier "top parent" (le premier niveau après le dossier racine 'json')
            if len(parts) >= 2 and parts[0] == "json":
                dossier_id = parts[1]
            elif len(parts) >= 2:
                dossier_id = parts[0]
            else:
                dossier_id = "inconnu"

            with zip_archive.open(file_info) as file:
                file_content = file.read().decode("utf-8")
                yield dossier_id, file_content
