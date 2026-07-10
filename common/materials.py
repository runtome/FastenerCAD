"""Fastener materials and their physical / mechanical properties.

The :class:`Material` dataclass is intentionally immutable so that registry
entries can be shared safely. Densities feed :meth:`FastenerBase.mass`; the
mechanical properties are provided for downstream strength calculations and are
not used by the geometry engine.

All values are nominal, at room temperature, in the following units:

* ``density``            -- g/cm^3
* ``youngs_modulus``     -- GPa
* ``yield_strength``     -- MPa
* ``tensile_strength``   -- MPa
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    """A fastener material with the properties needed for mass and strength.

    Attributes:
        name: Registry key / human-readable identifier (e.g. ``"steel-8.8"``).
        density: Mass density in g/cm^3.
        youngs_modulus: Young's modulus in GPa.
        yield_strength: 0.2% proof / yield strength in MPa.
        tensile_strength: Ultimate tensile strength in MPa.
        description: Free-form description of the grade.
    """

    name: str
    density: float
    youngs_modulus: float
    yield_strength: float
    tensile_strength: float
    description: str = ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_MATERIALS: dict[str, Material] = {
    m.name: m
    for m in (
        Material("steel-8.8", 7.85, 200.0, 640.0, 800.0, "Property class 8.8 carbon steel"),
        Material("steel-10.9", 7.85, 200.0, 940.0, 1040.0, "Property class 10.9 alloy steel"),
        Material("steel-12.9", 7.85, 200.0, 1100.0, 1220.0, "Property class 12.9 alloy steel"),
        Material(
            "stainless-a2-70", 8.00, 193.0, 450.0, 700.0, "A2-70 austenitic stainless (AISI 304)"
        ),
        Material(
            "stainless-a4-80", 8.00, 193.0, 600.0, 800.0, "A4-80 austenitic stainless (AISI 316)"
        ),
        Material("brass", 8.50, 100.0, 200.0, 400.0, "CuZn brass"),
        Material("aluminum", 2.70, 69.0, 240.0, 310.0, "6061-T6 aluminium alloy"),
        Material("titanium", 4.51, 114.0, 830.0, 900.0, "Ti-6Al-4V titanium alloy"),
    )
}

DEFAULT_MATERIAL = "steel-8.8"


def get_material(name: str) -> Material:
    """Return the registered :class:`Material` for ``name``.

    Args:
        name: Registry key, e.g. ``"steel-8.8"`` or ``"titanium"``.

    Returns:
        The matching :class:`Material`.

    Raises:
        KeyError: If ``name`` is not a registered material.
    """
    try:
        return _MATERIALS[name]
    except KeyError as exc:
        available = ", ".join(sorted(_MATERIALS))
        raise KeyError(f"Unknown material {name!r}. Available: {available}") from exc


def list_materials() -> list[str]:
    """Return the sorted names of all registered materials."""
    return sorted(_MATERIALS)


def register_material(material: Material) -> None:
    """Add or replace a material in the registry.

    Args:
        material: The material to register (keyed by its ``name``).
    """
    _MATERIALS[material.name] = material
