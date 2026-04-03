from dataclasses import dataclass
from datetime import date, datetime

from lib.bq_utils.models import BigQueryRow


@dataclass
class ScrutinRow(BigQueryRow):
    uid: str
