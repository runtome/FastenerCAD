"""STEP (ISO 10303) export.

Thin wrapper around :func:`cadquery.exporters.export` so that parts never touch
file I/O directly. STEP is the preferred exchange format: it preserves exact
(B-rep) geometry rather than a mesh approximation.
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
from cadquery import exporters


def export_step(model: cq.Workplane, path: str | Path) -> Path:
    """Export a model to a STEP file.

    Args:
        model: The CADQuery model to export.
        path: Destination file path (``.step`` / ``.stp``).

    Returns:
        The path written, as a :class:`pathlib.Path`.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(model, str(out), exportType="STEP")
    return out
