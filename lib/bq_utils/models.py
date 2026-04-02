from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any


@dataclass
class BigQueryRow:
    def to_bq_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key, value in payload.items():
            if isinstance(value, (date, datetime)):
                payload[key] = value.isoformat()
        return payload
