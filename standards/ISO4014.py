"""ISO 4014 -- Hexagon head bolts, partially threaded (product grades A and B)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from standards._hex_bolt import HexBoltBase


@dataclass
class HexBoltISO4014(HexBoltBase):
    """An ISO 4014 partially threaded hex head bolt.

    The threaded length ``b`` defaults to the ISO 4014 grip-length formula but
    may be overridden explicitly.

    Attributes:
        thread_length: Explicit threaded length ``b`` (mm); when ``None`` the
            ISO 4014 formula is used.
    """

    thread_length: float | None = None

    STANDARD: ClassVar[str] = "ISO 4014"
    PART: ClassVar[str] = "hex bolt"

    def _thread_length(self) -> float:
        """Return the threaded length ``b`` per ISO 4014 (or the override)."""
        if self.thread_length is not None:
            return self.thread_length
        diameter = self.entry.nominal_diameter
        if self.length <= 125.0:
            return 2.0 * diameter + 6.0
        if self.length <= 200.0:
            return 2.0 * diameter + 12.0
        return 2.0 * diameter + 25.0
