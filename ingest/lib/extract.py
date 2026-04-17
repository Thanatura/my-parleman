import io
import os
import tempfile
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


def fetch_zip_file_to_temp(url: str) -> str:
    response = requests.get(url, timeout=(5, 45), stream=True)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        body_preview = response.text[:200] if hasattr(response, "text") else ""
        raise ValueError(
            f"Failed to fetch file from {url}, status code: {response.status_code}, "
            f"response body (truncated): {body_preview}"
        ) from exc

    temp_file_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            temp_file_path = tmp_file.name
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    tmp_file.write(chunk)
    except Exception:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise

    return temp_file_path


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


def extract_zip_file_contents_with_folder(
    archive_path: str,
) -> Iterator[tuple[str, str]]:
    with zipfile.ZipFile(archive_path) as zip_archive:
        for file_info in zip_archive.infolist():
            if file_info.is_dir() or not file_info.filename.endswith(".json"):
                continue

            parts = file_info.filename.strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "json":
                dossier_id = parts[1]
            elif len(parts) >= 2:
                dossier_id = parts[0]
            else:
                dossier_id = "inconnu"

            with zip_archive.open(file_info) as file:
                file_content = file.read().decode("utf-8")
                yield dossier_id, file_content
