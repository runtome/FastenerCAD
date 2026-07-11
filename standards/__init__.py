"""Standardised fastener parts, one module per standard, plus a registry."""

from __future__ import annotations

from common.base import FastenerBase
from standards.DIN933 import HexBoltDIN933
from standards.DIN976 import ThreadedRodDIN976
from standards.ISO4014 import HexBoltISO4014
from standards.ISO4017 import HexScrewISO4017
from standards.ISO4032 import HexNutISO4032
from standards.ISO7089 import WasherISO7089
from standards.JIS_B1180 import HexBoltJISB1180

# Registry mapping a standard code to its part class.
STANDARDS: dict[str, type[FastenerBase]] = {
    HexBoltISO4014.STANDARD: HexBoltISO4014,
    HexScrewISO4017.STANDARD: HexScrewISO4017,
    HexNutISO4032.STANDARD: HexNutISO4032,
    HexBoltDIN933.STANDARD: HexBoltDIN933,
    HexBoltJISB1180.STANDARD: HexBoltJISB1180,
    WasherISO7089.STANDARD: WasherISO7089,
    ThreadedRodDIN976.STANDARD: ThreadedRodDIN976,
}


def get_standard(code: str) -> type[FastenerBase]:
    """Return the part class registered for a standard code.

    Args:
        code: Standard designation, e.g. ``"ISO 4014"`` or ``"DIN 933"``.

    Returns:
        The corresponding :class:`~common.base.FastenerBase` subclass.

    Raises:
        KeyError: If the code is not registered.
    """
    try:
        return STANDARDS[code]
    except KeyError as exc:
        available = ", ".join(sorted(STANDARDS))
        raise KeyError(f"Unknown standard {code!r}. Available: {available}") from exc


__all__ = [
    "STANDARDS",
    "HexBoltDIN933",
    "HexBoltISO4014",
    "HexBoltJISB1180",
    "HexNutISO4032",
    "HexScrewISO4017",
    "ThreadedRodDIN976",
    "WasherISO7089",
    "get_standard",
]
