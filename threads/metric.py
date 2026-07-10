"""ISO 68-1 metric thread geometry engine.

This module owns *all* thread geometry generation. It exposes:

* Profile math -- :func:`fundamental_height`, :func:`basic_pitch_diameter`,
  :func:`bolt_minor_diameter`, :func:`nut_minor_diameter` (ISO 68-1).
* Solid builders -- :func:`external_shaft` (a threaded cylinder for bolts/rods)
  and :func:`internal_thread_cut` (the negative solid subtracted from a nut
  blank to form a tapped hole).

Both builders support two modes:

* ``"cosmetic"`` -- a plain cylinder at the pitch diameter with a lead-in
  chamfer. Fast, robust, small files. This is the default everywhere.
* ``"real"`` -- a true helical thread swept from an ISO-style tooth profile.
  Geometrically accurate but slower to build and export.
"""

from __future__ import annotations

import math

import cadquery as cq
from cadquery import Plane, Vector

from common.dimensions import ThreadDimensions

# ISO 68-1 coefficients relative to pitch P.
_H_PER_P = math.sqrt(3.0) / 2.0  # fundamental triangle height H = 0.8660 * P
_D2_OFFSET = 0.6495  # d2 = d - 0.6495 * P
_D3_OFFSET = 1.2269  # bolt minor d3 = d - 1.2269 * P
_D1_OFFSET = 1.0825  # nut minor  D1 = d - 1.0825 * P

_MODE_COSMETIC = "cosmetic"
_MODE_REAL = "real"


# ---------------------------------------------------------------------------
# Profile math (ISO 68-1)
# ---------------------------------------------------------------------------


def fundamental_height(pitch: float) -> float:
    """Return the fundamental triangle height ``H = P * sqrt(3) / 2`` (mm)."""
    return _H_PER_P * pitch


def basic_pitch_diameter(nominal_diameter: float, pitch: float) -> float:
    """Return the basic pitch diameter ``d2 = d - 0.6495 * P`` (mm)."""
    return nominal_diameter - _D2_OFFSET * pitch


def bolt_minor_diameter(nominal_diameter: float, pitch: float) -> float:
    """Return the external (bolt) minor diameter ``d3 = d - 1.2269 * P`` (mm)."""
    return nominal_diameter - _D3_OFFSET * pitch


def nut_minor_diameter(nominal_diameter: float, pitch: float) -> float:
    """Return the internal (nut) minor diameter ``D1 = d - 1.0825 * P`` (mm)."""
    return nominal_diameter - _D1_OFFSET * pitch


# ---------------------------------------------------------------------------
# Helical thread construction (real mode)
# ---------------------------------------------------------------------------


def _tooth_profile(minor_r: float, major_r: float, pitch: float, lefthand: bool) -> cq.Workplane:
    """Build the swept tooth cross-section positioned at the helix start.

    The profile is a truncated ISO-style tooth drawn in the plane perpendicular
    to the helix tangent at its start point ``(minor_r, 0, 0)``.

    Args:
        minor_r: Core (minor) radius (mm).
        major_r: Crest (major) radius (mm).
        pitch: Thread pitch (mm).
        lefthand: Whether the mating helix is left-handed.

    Returns:
        A :class:`cadquery.Workplane` holding the closed profile wire.
    """
    depth = major_r - minor_r
    # Helix tangent at theta = 0: (0, +/-r, P / 2pi); sign flips for left-hand.
    axial_sign = -1.0 if lefthand else 1.0
    tangent = Vector(0.0, axial_sign * minor_r, pitch / (2.0 * math.pi)).normalized()
    plane = Plane(origin=(minor_r, 0.0, 0.0), xDir=(1.0, 0.0, 0.0), normal=tangent.toTuple())

    # Local coords: x = radial outward, y ~ axial. Truncated crest = P/8 flat.
    crest_half = pitch / 16.0
    root_half = pitch / 2.0
    return (
        cq.Workplane(plane)
        .polyline(
            [
                (0.0, -root_half),
                (depth, -crest_half),
                (depth, crest_half),
                (0.0, root_half),
            ]
        )
        .close()
    )


def _male_thread_solid(
    major_diameter: float,
    minor_diameter: float,
    pitch: float,
    length: float,
    lefthand: bool = False,
) -> cq.Workplane:
    """Build a solid male thread (core cylinder plus helical ridges).

    The helix is generated slightly over-length and the result is trimmed to
    ``[0, length]`` with flat ends.

    Args:
        major_diameter: Crest (major) diameter (mm).
        minor_diameter: Core (minor) diameter (mm).
        pitch: Thread pitch (mm).
        length: Threaded length along +Z (mm).
        lefthand: If ``True``, build a left-hand thread.

    Returns:
        The trimmed thread solid as a :class:`cadquery.Workplane`.
    """
    major_r = major_diameter / 2.0
    minor_r = minor_diameter / 2.0

    helix_len = length + 2.0 * pitch
    helix = cq.Wire.makeHelix(pitch=pitch, height=helix_len, radius=minor_r, lefthand=lefthand)
    path = cq.Workplane(obj=helix)

    ridges = _tooth_profile(minor_r, major_r, pitch, lefthand).sweep(path, isFrenet=True)
    # Drop by one pitch so the over-length turns straddle both trim planes.
    ridges = ridges.translate((0.0, 0.0, -pitch))

    core = cq.Workplane("XY").circle(minor_r).extrude(length)
    male = core.union(ridges)

    # Trim to flat ends at z = 0 and z = length.
    trim = cq.Workplane("XY").circle(major_r + 1.0).extrude(length)
    return male.intersect(trim)


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------


def _chamfer_free_ends(
    shaft: cq.Workplane, chamfer: float, top: bool, bottom: bool
) -> cq.Workplane:
    """Apply a lead-in chamfer to the top and/or bottom face of a shaft."""
    if chamfer <= 0:
        return shaft
    if top:
        shaft = shaft.faces(">Z").chamfer(chamfer)
    if bottom:
        shaft = shaft.faces("<Z").chamfer(chamfer)
    return shaft


def external_shaft(
    dims: ThreadDimensions,
    length: float,
    mode: str = _MODE_COSMETIC,
    chamfer_tip: bool = True,
    chamfer_start: bool = False,
    lefthand: bool = False,
) -> cq.Workplane:
    """Build an externally threaded cylinder along +Z from ``z = 0``.

    Args:
        dims: Thread dimensions for the size/series.
        length: Threaded length (mm).
        mode: ``"cosmetic"`` (pitch-diameter cylinder) or ``"real"`` (helix).
        chamfer_tip: Chamfer the free (top) end.
        chamfer_start: Chamfer the starting (bottom) end.
        lefthand: Build a left-hand thread (``"real"`` mode only).

    Returns:
        The threaded shaft as a :class:`cadquery.Workplane`.
    """
    if mode == _MODE_COSMETIC:
        radius = dims.pitch_diameter / 2.0
        chamfer = min(dims.pitch, radius * 0.6, length * 0.2)
        shaft = cq.Workplane("XY").circle(radius).extrude(length)
        return _chamfer_free_ends(shaft, chamfer, chamfer_tip, chamfer_start)
    if mode == _MODE_REAL:
        return _male_thread_solid(
            major_diameter=dims.nominal_diameter,
            minor_diameter=dims.minor_diameter_bolt,
            pitch=dims.pitch,
            length=length,
            lefthand=lefthand,
        )
    raise ValueError(f"Unknown thread mode {mode!r} (expected 'cosmetic' or 'real').")


def internal_thread_cut(
    dims: ThreadDimensions,
    length: float,
    mode: str = _MODE_COSMETIC,
    lefthand: bool = False,
) -> cq.Workplane:
    """Build the negative solid to subtract from a blank to form a tapped hole.

    Args:
        dims: Thread dimensions for the size/series.
        length: Hole depth along +Z (mm); typically the nut height.
        mode: ``"cosmetic"`` (pitch-diameter bore) or ``"real"`` (helical groove).
        lefthand: Build a left-hand thread (``"real"`` mode only).

    Returns:
        The cutting solid as a :class:`cadquery.Workplane`.
    """
    if mode == _MODE_COSMETIC:
        radius = dims.pitch_diameter / 2.0
        return cq.Workplane("XY").circle(radius).extrude(length)
    if mode == _MODE_REAL:
        # A plain bore at the nut minor diameter, plus a male thread whose ridges
        # carve the female grooves out to the major diameter.
        bore = cq.Workplane("XY").circle(dims.minor_diameter_nut / 2.0).extrude(length)
        ridges = _male_thread_solid(
            major_diameter=dims.nominal_diameter,
            minor_diameter=dims.minor_diameter_nut,
            pitch=dims.pitch,
            length=length,
            lefthand=lefthand,
        )
        return bore.union(ridges)
    raise ValueError(f"Unknown thread mode {mode!r} (expected 'cosmetic' or 'real').")
