"""Bolt + washer(s) + nut assembly."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from assemblies._base import AssemblyBase
from common.dimensions import load_entry
from common.materials import DEFAULT_MATERIAL
from common.utils import require_positive
from standards.ISO4014 import HexBoltISO4014
from standards.ISO4032 import HexNutISO4032
from standards.ISO7089 import WasherISO7089

_BOLT_COLOR = cq.Color(0.60, 0.60, 0.66)
_NUT_COLOR = cq.Color(0.70, 0.55, 0.35)
_WASHER_COLOR = cq.Color(0.75, 0.75, 0.78)


@dataclass
class BoltNutAssembly(AssemblyBase):
    """An ISO 4014 bolt fastened with an ISO 4032 nut and optional washers.

    The bolt is modelled tip-down (head at the top). The nut is threaded near the
    tip; ``clamp_length`` sets the grip distance from the head bearing face to the
    nut's upper face. Washers, when enabled, are placed under the head and under
    the nut.

    Attributes:
        size: Nominal size, e.g. ``"M10"``.
        length: Bolt shank length (mm).
        clamp_length: Grip length from the head bearing face to the nut (mm).
            Defaults to seating the nut near the tip.
        washers: Whether to include plain washers under the head and nut.
        thread: Thread mode, ``"cosmetic"`` or ``"real"``.
        thread_series: ``"coarse"`` or ``"fine"``.
        material: Material key applied to every component.
    """

    size: str
    length: float
    clamp_length: float | None = None
    washers: bool = False
    thread: str = "cosmetic"
    thread_series: str = "coarse"
    material: str = DEFAULT_MATERIAL

    def __post_init__(self) -> None:
        """Validate the bolt length."""
        require_positive(self.length, "length")

    def _build(self) -> cq.Assembly:
        """Build the positioned bolt/washer/nut assembly."""
        entry = load_entry(self.size)
        washer_t = entry.washer.thickness
        nut_h = entry.hex_nut.height
        length = self.length

        bolt = HexBoltISO4014(
            size=self.size,
            length=length,
            thread=self.thread,
            thread_series=self.thread_series,
            material=self.material,
        )
        nut = HexNutISO4032(
            size=self.size,
            thread=self.thread,
            thread_series=self.thread_series,
            material=self.material,
        )

        # Grip from the head bearing face (z = length) down to the nut's top face.
        washer_gap = washer_t if self.washers else 0.0
        default_grip = length - nut_h - washer_gap
        grip = self.clamp_length if self.clamp_length is not None else default_grip
        nut_top = length - grip
        nut_bottom = nut_top - nut_h
        if nut_bottom < 0.0:
            raise ValueError(
                f"clamp_length {grip} too large for length {length}: nut would extend past the tip."
            )

        asm = cq.Assembly(name=f"bolt_nut_{self.size}")
        asm.add(bolt.model, name="bolt", color=_BOLT_COLOR)
        asm.add(
            nut.model,
            name="nut",
            color=_NUT_COLOR,
            loc=cq.Location(cq.Vector(0.0, 0.0, nut_bottom)),
        )

        if self.washers:
            washer = WasherISO7089(size=self.size, material=self.material)
            # Under the head, on the shank (top face flush with the bearing face).
            asm.add(
                washer.model,
                name="washer_head",
                color=_WASHER_COLOR,
                loc=cq.Location(cq.Vector(0.0, 0.0, length - washer_t)),
            )
            # Under the nut (between the nut and the clamped members).
            asm.add(
                washer.model,
                name="washer_nut",
                color=_WASHER_COLOR,
                loc=cq.Location(cq.Vector(0.0, 0.0, nut_top)),
            )
        return asm
