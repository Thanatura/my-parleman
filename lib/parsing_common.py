import io
import json
import zipfile
from datetime import UTC, date, datetime
from typing import Any


def to_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def to_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def to_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return str(value).strip() == "1"


def utc_now() -> datetime:
    return datetime.now(UTC)


def read_json_files_from_zip(zip_bytes: bytes, prefix: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        file_names = [
            name
            for name in archive.namelist()
            if name.startswith(prefix) and name.endswith(".json")
        ]
        for file_name in file_names:
            payloads.append(json.loads(archive.read(file_name)))
    return payloads


def organe_refs(raw_organes: dict[str, Any]) -> list[str | None]:
    if not raw_organes:
        return []
    refs = raw_organes.get("organeRef", [])
    if isinstance(refs, str):
        return [refs]
    if not isinstance(refs, list):
        raise ValueError(f"Expected 'organeRef' to be a str or list, got {type(refs)}")
    return refs
