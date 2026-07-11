"""ISO 4017 -- Hexagon head screws, fully threaded (product grades A and B)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from standards._hex_bolt import HexBoltBase


@dataclass
class HexScrewISO4017(HexBoltBase):
    """An ISO 4017 fully threaded hex head screw.

    The thread runs the entire shank length, so there is no plain shank.
    """

    STANDARD: ClassVar[str] = "ISO 4017"
    PART: ClassVar[str] = "hex screw"

    def _thread_length(self) -> float:
        """Return the threaded length: the full shank length (fully threaded)."""
        return self.length
