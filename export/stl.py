"""STL (triangle mesh) export.

STL approximates the solid with a triangle mesh; the deflection parameters
control tessellation quality (smaller = finer mesh, larger files).
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
from cadquery import exporters


def export_stl(
    model: cq.Workplane,
    path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.2,
) -> Path:
    """Export a model to a binary STL mesh file.

    Args:
        model: The CADQuery model to export.
        path: Destination file path (``.stl``).
        tolerance: Maximum linear deflection of the mesh from the surface (mm).
        angular_tolerance: Maximum angular deflection between facets (rad).

    Returns:
        The path written, as a :class:`pathlib.Path`.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(
        model,
        str(out),
        exportType="STL",
        tolerance=tolerance,
        angularTolerance=angular_tolerance,
    )
    return out
