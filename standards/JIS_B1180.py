"""JIS B1180 -- Hexagon head bolts (Japanese Industrial Standard).

Geometrically a JIS B1180 hex bolt matches ISO 4014 except that the classic
(pre-ISO-harmonisation) appendix sizes use a larger width across flats for a few
diameters. Those divergences are captured in :data:`_JIS_WIDTH_ACROSS_FLATS`;
all other dimensions come from the shared catalog.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from standards.ISO4014 import HexBoltISO4014

# Nominal diameter (mm) -> JIS width across flats (mm) where it differs from ISO.
_JIS_WIDTH_ACROSS_FLATS: dict[float, float] = {
    10.0: 17.0,  # ISO 4014 uses 16.0
    12.0: 19.0,  # ISO 4014 uses 18.0
}


@dataclass
class HexBoltJISB1180(HexBoltISO4014):
    """A JIS B1180 hex bolt (ISO 4014 geometry with JIS head widths)."""

    STANDARD: ClassVar[str] = "JIS B1180"
    PART: ClassVar[str] = "hex bolt"

    def _head_width_across_flats(self) -> float:
        """Return the JIS head width across flats, overriding ISO where needed."""
        diameter = self.entry.nominal_diameter
        return _JIS_WIDTH_ACROSS_FLATS.get(diameter, super()._head_width_across_flats())
