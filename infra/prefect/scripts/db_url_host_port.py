#!/usr/bin/env python3
import os
from urllib.parse import urlsplit


def main() -> int:
    url = os.environ.get("PREFECT_API_DATABASE_CONNECTION_URL", "")
    parsed = urlsplit(url)
    host = parsed.hostname
    port = parsed.port or 5432

    if not host:
        return 1

    print(f"{host}:{port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
