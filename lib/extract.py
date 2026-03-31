import io
import zipfile

import requests


def fetch_zip_file(url: str) -> zipfile.ZipFile:
    print(f"Fetching file from {url}...")
    file = requests.get(url)
    print("Download complete, processing the zip archive...")
    zip_archive = zipfile.ZipFile(io.BytesIO(file.content))

    return zip_archive


def extract_file_contents(zip_archive: zipfile.ZipFile) -> list[str]:
    file_contents = []
    for file_info in zip_archive.infolist():
        with zip_archive.open(file_info) as file:
            content = file.read().decode("utf-8")
            file_contents.append(content)
    return file_contents
