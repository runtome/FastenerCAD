"""Common foundation: base class, dimension records, materials, tolerances, utils."""

from __future__ import annotations

from common.base import FastenerBase
from common.dimensions import (
    FastenerCatalogEntry,
    HexHeadDimensions,
    NutDimensions,
    ThreadDimensions,
    WasherDimensions,
    available_sizes,
    load_entry,
)
from common.materials import Material, get_material, list_materials
from common.tolerances import ToleranceClass

__all__ = [
    "FastenerBase",
    "FastenerCatalogEntry",
    "HexHeadDimensions",
    "Material",
    "NutDimensions",
    "ThreadDimensions",
    "ToleranceClass",
    "WasherDimensions",
    "available_sizes",
    "get_material",
    "list_materials",
    "load_entry",
]
