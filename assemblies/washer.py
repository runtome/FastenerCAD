"""Washer-stack assembly helper."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from assemblies._base import AssemblyBase
from common.dimensions import load_entry
from common.materials import DEFAULT_MATERIAL
from standards.ISO7089 import WasherISO7089

_WASHER_COLOR = cq.Color(0.75, 0.75, 0.78)


@dataclass
class WasherStack(AssemblyBase):
    """A vertical stack of identical ISO 7089 plain washers.

    Useful for building shims or as a spacer sub-assembly.

    Attributes:
        size: Nominal size, e.g. ``"M8"``.
        count: Number of washers in the stack (>= 1).
        material: Material key applied to every washer.
    """

    size: str
    count: int = 2
    material: str = DEFAULT_MATERIAL

    def __post_init__(self) -> None:
        """Validate the washer count."""
        if self.count < 1:
            raise ValueError(f"count must be >= 1, got {self.count}.")

    def _build(self) -> cq.Assembly:
        """Build the stacked-washer assembly."""
        thickness = load_entry(self.size).washer.thickness
        washer = WasherISO7089(size=self.size, material=self.material)

        asm = cq.Assembly(name=f"washer_stack_{self.size}_x{self.count}")
        for index in range(self.count):
            asm.add(
                washer.model,
                name=f"washer_{index}",
                color=_WASHER_COLOR,
                loc=cq.Location(cq.Vector(0.0, 0.0, index * thickness)),
            )
        return asm
