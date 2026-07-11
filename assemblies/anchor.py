"""Simplified anchor-bolt assembly."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from assemblies._base import AssemblyBase
from common.dimensions import load_entry
from common.materials import DEFAULT_MATERIAL
from common.utils import require_positive
from standards.DIN976 import ThreadedRodDIN976
from standards.ISO4032 import HexNutISO4032
from standards.ISO7089 import WasherISO7089

_STEEL_COLOR = cq.Color(0.60, 0.60, 0.66)
_NUT_COLOR = cq.Color(0.70, 0.55, 0.35)
_WASHER_COLOR = cq.Color(0.75, 0.75, 0.78)


@dataclass
class AnchorBoltAssembly(AssemblyBase):
    """A simplified wedge-style anchor bolt.

    Comprises a threaded rod (DIN 976) with a hex nut and washer at the exposed
    end and a tapered expansion sleeve at the embedded end. The sleeve is a
    schematic cone frustum rather than a detailed clip.

    Attributes:
        size: Nominal size, e.g. ``"M12"``.
        length: Overall rod length (mm).
        embedment: Length of the embedded (sleeve) end (mm).
        thread: Thread mode, ``"cosmetic"`` or ``"real"``.
        thread_series: ``"coarse"`` or ``"fine"``.
        material: Material key applied to every component.
    """

    size: str
    length: float
    embedment: float = 40.0
    thread: str = "cosmetic"
    thread_series: str = "coarse"
    material: str = DEFAULT_MATERIAL

    def __post_init__(self) -> None:
        """Validate lengths."""
        require_positive(self.length, "length")
        require_positive(self.embedment, "embedment")
        if self.embedment >= self.length:
            raise ValueError(f"embedment {self.embedment} must be less than length {self.length}.")

    def _build(self) -> cq.Assembly:
        """Build the anchor-bolt assembly."""
        entry = load_entry(self.size)
        diameter = entry.nominal_diameter
        washer_t = entry.washer.thickness
        nut_h = entry.hex_nut.height

        rod = ThreadedRodDIN976(
            size=self.size,
            length=self.length,
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
        washer = WasherISO7089(size=self.size, material=self.material)

        # Tapered expansion sleeve over the embedded end (z = 0 .. embedment).
        sleeve = (
            cq.Workplane("XY")
            .circle(diameter * 0.75)
            .workplane(offset=self.embedment)
            .circle(diameter * 0.55)
            .loft(combine=True)
        )

        asm = cq.Assembly(name=f"anchor_{self.size}")
        asm.add(rod.model, name="rod", color=_STEEL_COLOR)
        asm.add(sleeve, name="sleeve", color=_STEEL_COLOR)
        # Washer and nut at the exposed top end.
        asm.add(
            washer.model,
            name="washer",
            color=_WASHER_COLOR,
            loc=cq.Location(cq.Vector(0.0, 0.0, self.length - nut_h - washer_t)),
        )
        asm.add(
            nut.model,
            name="nut",
            color=_NUT_COLOR,
            loc=cq.Location(cq.Vector(0.0, 0.0, self.length - nut_h)),
        )
        return asm
