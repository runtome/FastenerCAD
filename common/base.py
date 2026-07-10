"""The common base class for every fastener part.

:class:`FastenerBase` centralises everything a part needs except its geometry:
parameter validation, catalog/thread/tolerance/material lookup, model caching,
mass / volume / bounding-box computation, and export delegation. Concrete parts
(bolts, nuts, washers, rods) subclass it and implement only :meth:`_build`.

The class is a keyword-only dataclass so that subclasses may freely add their own
positional fields (e.g. ``length``) without dataclass default-ordering conflicts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import cadquery as cq

from common.dimensions import FastenerCatalogEntry, ThreadDimensions, load_entry
from common.materials import DEFAULT_MATERIAL, get_material
from common.tolerances import ToleranceClass
from common.utils import require_choice

THREAD_MODES: tuple[str, ...] = ("cosmetic", "real")
THREAD_SERIES: tuple[str, ...] = ("coarse", "fine")

# STL export defaults (linear / angular deflection).
_STL_TOLERANCE = 0.05
_STL_ANGULAR_TOLERANCE = 0.2


@dataclass(kw_only=True)
class FastenerBase(ABC):
    """Abstract base class for all fasteners.

    Attributes:
        size: Nominal size designation, e.g. ``"M8"``.
        thread: Thread modelling mode, ``"cosmetic"`` (default) or ``"real"``.
        thread_series: Thread series, ``"coarse"`` (default) or ``"fine"``.
        material: Material registry key used for :meth:`mass` (default steel 8.8).
        tolerance: ISO 965 thread tolerance class, e.g. ``"6g"`` (external) or
            ``"6H"`` (internal).
    """

    size: str
    thread: str = "cosmetic"
    thread_series: str = "coarse"
    material: str = DEFAULT_MATERIAL
    tolerance: str = "6g"

    def __post_init__(self) -> None:
        """Validate shared parameters after dataclass initialisation."""
        require_choice(self.thread, THREAD_MODES, "thread")
        require_choice(self.thread_series, THREAD_SERIES, "thread_series")
        get_material(self.material)  # raises KeyError for unknown materials
        ToleranceClass.parse(self.tolerance)  # raises ValueError if malformed
        load_entry(self.size)  # raises FileNotFoundError for unknown sizes

    # -- Catalog / spec access ---------------------------------------------

    @property
    def entry(self) -> FastenerCatalogEntry:
        """The catalog entry (all dimensions) for this part's size."""
        return load_entry(self.size)

    @property
    def thread_dimensions(self) -> ThreadDimensions:
        """Thread dimensions for this part's size and series."""
        return self.entry.thread(self.thread_series)

    @property
    def tolerance_class(self) -> ToleranceClass:
        """The parsed ISO 965 tolerance class for this part."""
        return ToleranceClass.parse(self.tolerance)

    # -- Geometry -----------------------------------------------------------

    @abstractmethod
    def _build(self) -> cq.Workplane:
        """Build and return the part geometry.

        Subclasses implement this using the catalog dimensions exposed via
        :attr:`entry` / :attr:`thread_dimensions`. It is called at most once; the
        result is cached in :attr:`model`.

        Returns:
            The part solid as a :class:`cadquery.Workplane`.
        """
        raise NotImplementedError

    @cached_property
    def model(self) -> cq.Workplane:
        """The built (and cached) CADQuery model for this part."""
        return self._build()

    # -- Derived quantities -------------------------------------------------

    def volume(self) -> float:
        """Return the solid volume in cubic millimetres."""
        return sum(solid.Volume() for solid in self.model.solids().vals())

    def mass(self) -> float:
        """Return the part mass in grams, using the configured material density."""
        density = get_material(self.material).density  # g/cm^3
        volume_cm3 = self.volume() / 1000.0
        return volume_cm3 * density

    def bounding_box(self) -> tuple[float, float, float]:
        """Return the axis-aligned bounding box size ``(dx, dy, dz)`` in mm."""
        bb = self.model.val().BoundingBox()
        return (bb.xlen, bb.ylen, bb.zlen)

    # -- Export -------------------------------------------------------------

    def to_step(self, path: str | Path) -> Path:
        """Export the part to a STEP file.

        Args:
            path: Destination file path.

        Returns:
            The path written.
        """
        from export.step import export_step

        return export_step(self.model, path)

    def to_stl(
        self,
        path: str | Path,
        tolerance: float = _STL_TOLERANCE,
        angular_tolerance: float = _STL_ANGULAR_TOLERANCE,
    ) -> Path:
        """Export the part to an STL mesh file.

        Args:
            path: Destination file path.
            tolerance: Linear deflection (mm).
            angular_tolerance: Angular deflection (rad).

        Returns:
            The path written.
        """
        from export.stl import export_stl

        return export_stl(self.model, path, tolerance, angular_tolerance)

    def to_dxf(self, path: str | Path) -> Path:
        """Export a 2D DXF projection of the part.

        Args:
            path: Destination file path.

        Returns:
            The path written.
        """
        from export.dxf import export_dxf

        return export_dxf(self.model, path)

    def save(self, path: str | Path) -> Path:
        """Export by inferring the format from the file suffix.

        Args:
            path: Destination path ending in ``.step``/``.stp``, ``.stl``, or
                ``.dxf``.

        Returns:
            The path written.

        Raises:
            ValueError: If the suffix is not a supported export format.
        """
        suffix = Path(path).suffix.lower()
        if suffix in (".step", ".stp"):
            return self.to_step(path)
        if suffix == ".stl":
            return self.to_stl(path)
        if suffix == ".dxf":
            return self.to_dxf(path)
        raise ValueError(f"Unsupported export suffix {suffix!r} (use .step, .stl, or .dxf).")
