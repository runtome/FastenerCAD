"""Reusable geometry and validation helpers.

These helpers are shared by every part builder so that hexagon construction,
head chamfering, and argument validation are defined exactly once.
"""

from __future__ import annotations

import math

import cadquery as cq

# 2 / sqrt(3): hexagon width-across-corners to width-across-flats ratio.
_AF_TO_AC = 2.0 / math.sqrt(3.0)


def across_flats_to_across_corners(width_across_flats: float) -> float:
    """Convert a hexagon width across flats ``s`` to width across corners ``e``.

    Args:
        width_across_flats: Distance between opposite flats (mm).

    Returns:
        Distance between opposite corners (mm).
    """
    return width_across_flats * _AF_TO_AC


def require_positive(value: float, name: str) -> float:
    """Validate that ``value`` is strictly positive.

    Args:
        value: The numeric value to check.
        name: Parameter name used in the error message.

    Returns:
        The validated value (unchanged).

    Raises:
        ValueError: If ``value`` is not strictly positive.
    """
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value}.")
    return value


def require_choice(value: str, choices: tuple[str, ...], name: str) -> str:
    """Validate that ``value`` is one of the allowed ``choices``.

    Args:
        value: The value to check.
        choices: Allowed values.
        name: Parameter name used in the error message.

    Returns:
        The validated value (unchanged).

    Raises:
        ValueError: If ``value`` is not in ``choices``.
    """
    if value not in choices:
        allowed = ", ".join(choices)
        raise ValueError(f"{name} must be one of {{{allowed}}}, got {value!r}.")
    return value


def hex_prism(width_across_flats: float, height: float, workplane: str = "XY") -> cq.Workplane:
    """Build a regular hexagonal prism centred on the origin.

    The prism is extruded from the workplane in the +normal direction. Two flats
    are parallel to the workplane's X axis.

    Args:
        width_across_flats: Distance between opposite flats (mm).
        height: Extrusion height (mm).
        workplane: Base workplane name (default ``"XY"``).

    Returns:
        A :class:`cadquery.Workplane` containing the hex prism solid.
    """
    require_positive(width_across_flats, "width_across_flats")
    require_positive(height, "height")
    across_corners = across_flats_to_across_corners(width_across_flats)
    return cq.Workplane(workplane).polygon(6, across_corners).extrude(height)


def chamfer_hex_head(
    head: cq.Workplane,
    width_across_flats: float,
    height: float,
    chamfer_angle_deg: float = 30.0,
) -> cq.Workplane:
    """Apply the ISO-style conical top chamfer to a hex head prism.

    The chamfer removes the six top corners, leaving a circular top face whose
    diameter equals the width across flats -- the characteristic look of an ISO
    hex head. Implemented as an intersection with a revolved cutting profile so
    the result is a true cone rather than six flat facets.

    Args:
        head: A hex prism (e.g. from :func:`hex_prism`) extruded +Z from ``z=0``.
        width_across_flats: Hex width across flats ``s`` (mm).
        height: Height of the head along Z (mm).
        chamfer_angle_deg: Chamfer face angle from the horizontal (mm),
            default 30 degrees per typical ISO practice.

    Returns:
        The chamfered head as a :class:`cadquery.Workplane`.
    """
    flats_radius = width_across_flats / 2.0
    corner_radius = across_flats_to_across_corners(width_across_flats) / 2.0
    chamfer_height = (corner_radius - flats_radius) * math.tan(math.radians(chamfer_angle_deg))
    # Keep the chamfer within the head; clamp if the head is very short.
    chamfer_height = min(chamfer_height, height)

    # Revolved cutting tool: full corner radius up to the chamfer start, then a
    # cone tapering inward to the flats radius at the top face.
    tool = (
        cq.Workplane("XZ")
        .moveTo(0.0, 0.0)
        .lineTo(corner_radius, 0.0)
        .lineTo(corner_radius, height - chamfer_height)
        .lineTo(flats_radius, height)
        .lineTo(0.0, height)
        .close()
        .revolve(360.0, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    )
    return head.intersect(tool)


def make_helix_wire(
    pitch: float,
    height: float,
    radius: float,
    lefthand: bool = False,
) -> cq.Wire:
    """Create a cylindrical helix wire, used as the sweep path for real threads.

    Args:
        pitch: Axial advance per revolution (mm).
        height: Total axial length of the helix (mm).
        radius: Helix radius (mm).
        lefthand: If ``True``, generate a left-hand helix.

    Returns:
        A :class:`cadquery.Wire` describing the helix along +Z.
    """
    require_positive(pitch, "pitch")
    require_positive(height, "height")
    require_positive(radius, "radius")
    return cq.Wire.makeHelix(pitch=pitch, height=height, radius=radius, lefthand=lefthand)
