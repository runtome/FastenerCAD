"""DXF (2D drawing) export.

DXF is a 2D format, so a 3D solid must first be reduced to a planar profile.
This module takes a horizontal mid-height section through the part (the plane
``z = height / 2``) and exports the resulting cross-section, which yields a
useful, well-defined 2D outline for drafting and laser/water-jet workflows.
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
from cadquery import exporters

from common.utils import as_shape


def export_dxf(model: cq.Workplane, path: str | Path, section_height: float | None = None) -> Path:
    """Export a horizontal cross-section of a model to a DXF file.

    Args:
        model: The CADQuery model to export.
        path: Destination file path (``.dxf``).
        section_height: Absolute Z height of the section plane. When ``None``,
            the part's mid-height is used.

    Returns:
        The path written, as a :class:`pathlib.Path`.

    Raises:
        ValueError: If the section plane does not intersect the solid.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    bb = as_shape(model).BoundingBox()
    # Models are built on the XY plane at z = 0, so the section offset equals the
    # absolute Z height.
    z = bb.zmin + (bb.zlen / 2.0) if section_height is None else section_height

    section = model.section(z)
    if not section.faces().vals():
        raise ValueError(f"Section plane at z={z} does not intersect the model.")

    exporters.export(section, str(out), exportType="DXF")
    return out
