"""ISO 7089 -- Plain washers, normal series, product grade A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import cadquery as cq

from common.base import FastenerBase


@dataclass
class WasherISO7089(FastenerBase):
    """An ISO 7089 plain washer (flat annular ring).

    Washers are unthreaded; the ``thread`` and ``tolerance`` parameters are
    accepted for API uniformity but do not affect the geometry.
    """

    STANDARD: ClassVar[str] = "ISO 7089"
    PART: ClassVar[str] = "washer"

    def _build(self) -> cq.Workplane:
        """Build the washer solid (outer disc with a concentric bore)."""
        washer = self.entry.washer
        return (
            cq.Workplane("XY")
            .circle(washer.outer_diameter / 2.0)
            .circle(washer.inner_diameter / 2.0)
            .extrude(washer.thickness)
        )
