"""DIN 933 -- Hexagon head set screws / bolts, fully threaded.

DIN 933 is functionally equivalent to ISO 4017 for the sizes covered here, so
this class reuses the ISO 4017 geometry entirely and only re-labels the standard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from standards.ISO4017 import HexScrewISO4017


@dataclass
class HexBoltDIN933(HexScrewISO4017):
    """A DIN 933 fully threaded hex bolt (geometry identical to ISO 4017)."""

    STANDARD: ClassVar[str] = "DIN 933"
    PART: ClassVar[str] = "hex bolt"
