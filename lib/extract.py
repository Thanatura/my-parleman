import io
import zipfile

import requests


def fetch_zip_file(url: str) -> bytes:
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(
            f"Failed to fetch file from {url}, status code: {response.status_code}"
        )
    return response.content


def extract_file_contents(archive_content: bytes) -> list[str]:
    zip_archive = zipfile.ZipFile(io.BytesIO(archive_content))
    file_contents = []
    for file_info in zip_archive.infolist():
        with zip_archive.open(file_info) as file:
            file_content = file.read().decode("utf-8")
            file_contents.append(file_content)
    return file_contents
