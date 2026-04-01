"""Per-table parsers for AN open data."""

from lib.parsing.acteurs import parse_acteurs
from lib.parsing.adresses import parse_adresses
from lib.parsing.deports import parse_deports
from lib.parsing.mandats import parse_mandats
from lib.parsing.organes import parse_organes

__all__ = [
    "parse_acteurs",
    "parse_adresses",
    "parse_mandats",
    "parse_organes",
    "parse_deports",
]
