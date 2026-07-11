"""Typed dimension records and the JSON catalog loader.

All fastener dimensions live in ``catalog/*.json`` (one file per size). This
module parses those files into immutable, type-checked dataclasses so that the
geometry code in :mod:`standards` never touches raw dictionaries or literal
numbers. Loading is cached, so repeated part construction is cheap.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import cache, lru_cache
from pathlib import Path
from typing import Any

# The catalog ships beside the source tree in development and as package data
# ("fastenercad_catalog") once installed. Prefer whichever exists.
_DEV_CATALOG = Path(__file__).resolve().parent.parent / "catalog"
_INSTALLED_CATALOG = Path(__file__).resolve().parent.parent / "fastenercad_catalog"

# 2 / sqrt(3): ratio of hexagon width-across-corners to width-across-flats.
_AF_TO_AC = 2.0 / math.sqrt(3.0)


def _catalog_dir() -> Path:
    """Return the directory that holds the dimension catalog JSON files."""
    if _DEV_CATALOG.is_dir():
        return _DEV_CATALOG
    if _INSTALLED_CATALOG.is_dir():
        return _INSTALLED_CATALOG
    raise FileNotFoundError(
        "Could not locate the dimension catalog directory "
        f"(looked in {_DEV_CATALOG} and {_INSTALLED_CATALOG})."
    )


@dataclass(frozen=True, slots=True)
class ThreadDimensions:
    """Metric thread dimensions for one pitch, per ISO 68-1 / ISO 261.

    Attributes:
        nominal_diameter: Nominal (major) diameter ``d`` in mm.
        pitch: Thread pitch ``P`` in mm.
        pitch_diameter: Pitch diameter ``d2`` in mm.
        minor_diameter_bolt: External minor diameter ``d3`` in mm (bolt/screw).
        minor_diameter_nut: Internal minor diameter ``D1`` in mm (nut).
        series: ``"coarse"`` or ``"fine"``.
    """

    nominal_diameter: float
    pitch: float
    pitch_diameter: float
    minor_diameter_bolt: float
    minor_diameter_nut: float
    series: str

    @property
    def thread_depth(self) -> float:
        """Radial engagement depth of the basic profile, ``(d - D1) / 2`` (mm)."""
        return (self.nominal_diameter - self.minor_diameter_nut) / 2.0


@dataclass(frozen=True, slots=True)
class HexHeadDimensions:
    """Hex bolt/screw head dimensions (ISO 4014 / ISO 4017 / DIN 933)."""

    width_across_flats: float
    head_height: float

    @property
    def width_across_corners(self) -> float:
        """Width across corners ``e`` derived from width across flats ``s``."""
        return self.width_across_flats * _AF_TO_AC


@dataclass(frozen=True, slots=True)
class NutDimensions:
    """Hex nut dimensions (ISO 4032, style 1)."""

    width_across_flats: float
    height: float

    @property
    def width_across_corners(self) -> float:
        """Width across corners ``e`` derived from width across flats ``s``."""
        return self.width_across_flats * _AF_TO_AC


@dataclass(frozen=True, slots=True)
class WasherDimensions:
    """Plain washer dimensions (ISO 7089)."""

    inner_diameter: float
    outer_diameter: float
    thickness: float


@dataclass(frozen=True, slots=True)
class FastenerCatalogEntry:
    """All dimensions for a single nominal size (e.g. ``M6``).

    Attributes:
        designation: Size designation, e.g. ``"M6"``.
        nominal_diameter: Nominal diameter ``d`` in mm.
        thread_coarse: Coarse-series thread dimensions.
        thread_fine: Fine-series thread dimensions (one entry per fine pitch).
        hex_head: Hex head dimensions.
        hex_nut: Hex nut dimensions.
        washer: Plain washer dimensions.
    """

    designation: str
    nominal_diameter: float
    thread_coarse: ThreadDimensions
    thread_fine: tuple[ThreadDimensions, ...]
    hex_head: HexHeadDimensions
    hex_nut: NutDimensions
    washer: WasherDimensions

    def thread(self, series: str = "coarse", pitch: float | None = None) -> ThreadDimensions:
        """Return the thread dimensions for a series (and optional exact pitch).

        Args:
            series: ``"coarse"`` or ``"fine"``.
            pitch: When ``series="fine"`` and multiple fine pitches exist, select
                the one matching this pitch. Ignored for the coarse series.

        Returns:
            The matching :class:`ThreadDimensions`.

        Raises:
            ValueError: If the series is unknown or no matching fine pitch exists.
        """
        if series == "coarse":
            return self.thread_coarse
        if series == "fine":
            if not self.thread_fine:
                raise ValueError(f"{self.designation} has no fine thread series.")
            if pitch is None:
                return self.thread_fine[0]
            for candidate in self.thread_fine:
                if math.isclose(candidate.pitch, pitch, abs_tol=1e-6):
                    return candidate
            available = ", ".join(f"{t.pitch}" for t in self.thread_fine)
            raise ValueError(
                f"{self.designation} has no fine pitch {pitch} mm (available: {available})."
            )
        raise ValueError(f"Unknown thread series {series!r} (expected 'coarse' or 'fine').")


def _thread_from_dict(nominal: float, series: str, data: dict[str, Any]) -> ThreadDimensions:
    """Build a :class:`ThreadDimensions` from a catalog thread sub-dict."""
    return ThreadDimensions(
        nominal_diameter=nominal,
        pitch=float(data["pitch"]),
        pitch_diameter=float(data["pitch_dia"]),
        minor_diameter_bolt=float(data["minor_dia_bolt"]),
        minor_diameter_nut=float(data["minor_dia_nut"]),
        series=series,
    )


def _entry_from_dict(data: dict[str, Any]) -> FastenerCatalogEntry:
    """Build a :class:`FastenerCatalogEntry` from a parsed catalog JSON dict."""
    nominal = float(data["nominal_diameter"])
    thread = data["thread"]
    fine = tuple(_thread_from_dict(nominal, "fine", f) for f in thread.get("fine", []))
    head = data["hex_head"]
    nut = data["hex_nut"]
    washer = data["washer"]
    return FastenerCatalogEntry(
        designation=str(data["designation"]),
        nominal_diameter=nominal,
        thread_coarse=_thread_from_dict(nominal, "coarse", thread["coarse"]),
        thread_fine=fine,
        hex_head=HexHeadDimensions(
            width_across_flats=float(head["width_across_flats"]),
            head_height=float(head["head_height"]),
        ),
        hex_nut=NutDimensions(
            width_across_flats=float(nut["width_across_flats"]),
            height=float(nut["height"]),
        ),
        washer=WasherDimensions(
            inner_diameter=float(washer["inner_dia"]),
            outer_diameter=float(washer["outer_dia"]),
            thickness=float(washer["thickness"]),
        ),
    )


@cache
def load_entry(size: str) -> FastenerCatalogEntry:
    """Load and cache the catalog entry for a nominal size.

    Args:
        size: Size designation such as ``"M6"`` or ``"M1.6"``.

    Returns:
        The parsed :class:`FastenerCatalogEntry`.

    Raises:
        FileNotFoundError: If no catalog file exists for the size.
    """
    path = _catalog_dir() / f"{size}.json"
    if not path.is_file():
        available = ", ".join(available_sizes())
        raise FileNotFoundError(f"No catalog entry for {size!r}. Available: {available}")
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return _entry_from_dict(data)


@lru_cache(maxsize=1)
def available_sizes() -> tuple[str, ...]:
    """Return all catalog sizes, sorted by nominal diameter."""
    files = _catalog_dir().glob("M*.json")
    sizes = [p.stem for p in files]
    return tuple(sorted(sizes, key=lambda s: float(s[1:])))
