"""ISO 261 metric coarse-pitch reference table.

The coarse pitch is the single standard pitch associated with each nominal
diameter. These values are the authoritative source used to generate the
dimension catalog and to validate it.
"""

from __future__ import annotations

# Nominal diameter (mm) -> coarse pitch (mm), ISO 261.
COARSE_PITCH: dict[float, float] = {
    1.6: 0.35,
    2.0: 0.40,
    2.5: 0.45,
    3.0: 0.50,
    4.0: 0.70,
    5.0: 0.80,
    6.0: 1.00,
    8.0: 1.25,
    10.0: 1.50,
    12.0: 1.75,
    16.0: 2.00,
    20.0: 2.50,
    24.0: 3.00,
    30.0: 3.50,
    36.0: 4.00,
    42.0: 4.50,
    48.0: 5.00,
    56.0: 5.50,
    64.0: 6.00,
}

# Nominal diameters covered by the library, ascending.
NOMINAL_DIAMETERS: tuple[float, ...] = tuple(sorted(COARSE_PITCH))


def coarse_pitch(nominal_diameter: float) -> float:
    """Return the coarse pitch for a nominal diameter.

    Args:
        nominal_diameter: Nominal diameter ``d`` in mm (e.g. ``6.0`` for M6).

    Returns:
        The coarse pitch in mm.

    Raises:
        KeyError: If the diameter is not in the coarse table.
    """
    try:
        return COARSE_PITCH[nominal_diameter]
    except KeyError as exc:
        available = ", ".join(str(d) for d in NOMINAL_DIAMETERS)
        raise KeyError(
            f"No coarse pitch for nominal diameter {nominal_diameter}. Available: {available}"
        ) from exc
