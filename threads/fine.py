"""ISO 261 metric fine-pitch reference table.

Each nominal diameter may have several standardised fine pitches. They are
listed here in descending pitch order with the most common ("preferred") fine
pitch first, which is the one selected by default.
"""

from __future__ import annotations

# Nominal diameter (mm) -> fine pitches (mm), preferred first.
FINE_PITCHES: dict[float, tuple[float, ...]] = {
    1.6: (0.20,),
    2.0: (0.25,),
    2.5: (0.35,),
    3.0: (0.35,),
    4.0: (0.50,),
    5.0: (0.50,),
    6.0: (0.75,),
    8.0: (1.00, 0.75),
    10.0: (1.25, 1.00, 0.75),
    12.0: (1.50, 1.25, 1.00),
    16.0: (1.50, 1.00),
    20.0: (1.50, 1.00),
    24.0: (2.00, 1.50, 1.00),
    30.0: (2.00, 1.50, 1.00),
    36.0: (3.00, 2.00, 1.50),
    42.0: (3.00, 2.00, 1.50),
    48.0: (3.00, 2.00, 1.50),
    56.0: (4.00, 3.00, 2.00),
    64.0: (4.00, 3.00, 2.00),
}


def fine_pitches(nominal_diameter: float) -> tuple[float, ...]:
    """Return all standard fine pitches for a nominal diameter (preferred first).

    Args:
        nominal_diameter: Nominal diameter ``d`` in mm.

    Returns:
        A tuple of fine pitches in mm; empty if the diameter has none.
    """
    return FINE_PITCHES.get(nominal_diameter, ())


def primary_fine_pitch(nominal_diameter: float) -> float:
    """Return the preferred (primary) fine pitch for a nominal diameter.

    Args:
        nominal_diameter: Nominal diameter ``d`` in mm.

    Returns:
        The preferred fine pitch in mm.

    Raises:
        KeyError: If the diameter has no fine pitches defined.
    """
    pitches = fine_pitches(nominal_diameter)
    if not pitches:
        raise KeyError(f"No fine pitch defined for nominal diameter {nominal_diameter}.")
    return pitches[0]
