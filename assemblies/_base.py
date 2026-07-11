"""Shared base class for multi-part assemblies.

:class:`AssemblyBase` mirrors :class:`~common.base.FastenerBase` but for models
made of several positioned parts. It wraps a :class:`cadquery.Assembly` (which
keeps per-part names and colours in STEP output) and delegates STL/DXF export to
a flattened compound of the same geometry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path

import cadquery as cq

from common.utils import as_shape, iter_solids


class AssemblyBase(ABC):
    """Abstract base for positioned multi-part assemblies."""

    @abstractmethod
    def _build(self) -> cq.Assembly:
        """Build and return the CADQuery assembly (called once, then cached)."""
        raise NotImplementedError

    @cached_property
    def assembly(self) -> cq.Assembly:
        """The built (and cached) :class:`cadquery.Assembly`."""
        return self._build()

    def compound(self) -> cq.Workplane:
        """Return the assembly flattened into a single compound solid."""
        return cq.Workplane(obj=self.assembly.toCompound())

    # -- Derived quantities -------------------------------------------------

    def volume(self) -> float:
        """Return the total solid volume of all components in cubic mm."""
        return sum(solid.Volume() for solid in iter_solids(self.compound()))

    def bounding_box(self) -> tuple[float, float, float]:
        """Return the axis-aligned bounding box size ``(dx, dy, dz)`` in mm."""
        bb = as_shape(self.compound()).BoundingBox()
        return (bb.xlen, bb.ylen, bb.zlen)

    # -- Export -------------------------------------------------------------

    def to_step(self, path: str | Path) -> Path:
        """Export the assembly to STEP, preserving per-part names and colours."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.assembly.export(str(out), exportType="STEP")
        return out

    def to_stl(
        self, path: str | Path, tolerance: float = 0.05, angular_tolerance: float = 0.2
    ) -> Path:
        """Export the flattened assembly to an STL mesh file."""
        from export.stl import export_stl

        return export_stl(self.compound(), path, tolerance, angular_tolerance)

    def to_dxf(self, path: str | Path) -> Path:
        """Export a 2D DXF section of the flattened assembly."""
        from export.dxf import export_dxf

        return export_dxf(self.compound(), path)

    def save(self, path: str | Path) -> Path:
        """Export by inferring the format from the file suffix.

        Args:
            path: Destination path ending in ``.step``/``.stp``, ``.stl``, or
                ``.dxf``.

        Returns:
            The path written.

        Raises:
            ValueError: If the suffix is not a supported export format.
        """
        suffix = Path(path).suffix.lower()
        if suffix in (".step", ".stp"):
            return self.to_step(path)
        if suffix == ".stl":
            return self.to_stl(path)
        if suffix == ".dxf":
            return self.to_dxf(path)
        raise ValueError(f"Unsupported export suffix {suffix!r} (use .step, .stl, or .dxf).")
