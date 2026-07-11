"""ISO 4032 -- Hexagon nuts, style 1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import cadquery as cq

from common.base import FastenerBase
from common.utils import chamfer_hex, hex_prism
from threads import ThreadProfile


@dataclass
class HexNutISO4032(FastenerBase):
    """An ISO 4032 style-1 hex nut.

    Modelled as a hex prism chamfered on both faces with a tapped through-hole.
    Defaults to the ``6H`` internal thread tolerance class.
    """

    # Nuts are internally threaded, so override the default tolerance to 6H.
    tolerance: str = field(default="6H", kw_only=True)

    STANDARD: ClassVar[str] = "ISO 4032"
    PART: ClassVar[str] = "hex nut"

    def _build(self) -> cq.Workplane:
        """Build the hex nut solid (chamfered hex blank minus a tapped hole)."""
        nut = self.entry.hex_nut
        width_across_flats = nut.width_across_flats
        height = nut.height

        blank = chamfer_hex(
            hex_prism(width_across_flats, height),
            width_across_flats,
            height,
            chamfer_top=True,
            chamfer_bottom=True,
        )
        thread = ThreadProfile.from_size(self.size, self.thread_series, mode=self.thread)
        return blank.cut(thread.internal_cut(height))
