"""ISO 965 metric-thread tolerance classes.

This module models the *fundamental deviation* (position of the tolerance zone
relative to the basic profile) for the tolerance positions commonly used on
fasteners. The magnitude of the tolerance zone (grade number, e.g. the ``6`` in
``6g``) affects manufacturing limits but has negligible effect on nominal solid
geometry, so only the fundamental deviation is applied to the model.

Fundamental deviations follow ISO 965-1 and are functions of the thread pitch
``P`` (mm). Results here are returned in millimetres.

External thread positions (applied to bolts/screws, deviation ``es`` <= 0):

============  =========================
Position      Fundamental deviation ``es`` (um)
============  =========================
``e``         -(50 + 11 * P)
``f``         -(30 + 11 * P)
``g``         -(15 + 11 * P)
``h``         0
============  =========================

Internal thread positions (applied to nuts, deviation ``EI`` >= 0):

============  =========================
Position      Fundamental deviation ``EI`` (um)
============  =========================
``G``         +(15 + 11 * P)
``H``         0
============  =========================
"""

from __future__ import annotations

from dataclasses import dataclass

# Fundamental-deviation coefficients keyed by tolerance position letter.
# Value is (constant_um, pitch_coefficient_um_per_mm); sign applied per position.
_EXTERNAL_ES: dict[str, tuple[float, float]] = {
    "e": (50.0, 11.0),
    "f": (30.0, 11.0),
    "g": (15.0, 11.0),
    "h": (0.0, 0.0),
}
_INTERNAL_EI: dict[str, tuple[float, float]] = {
    "G": (15.0, 11.0),
    "H": (0.0, 0.0),
}


@dataclass(frozen=True, slots=True)
class ToleranceClass:
    """A parsed ISO 965 thread tolerance class such as ``6g`` or ``6H``.

    Attributes:
        designation: Original designation, e.g. ``"6g"`` or ``"6H"``.
        grade: The IT tolerance grade number (e.g. ``6``).
        position: The single-letter tolerance position (e.g. ``"g"`` or ``"H"``).
        is_external: ``True`` for external threads (bolts), ``False`` for
            internal threads (nuts). Determined by the case of ``position``.
    """

    designation: str
    grade: int
    position: str
    is_external: bool

    @classmethod
    def parse(cls, designation: str) -> ToleranceClass:
        """Parse a designation like ``"6g"`` or ``"6H"`` into a class instance.

        Args:
            designation: Tolerance class designation (grade digits followed by a
                single position letter), e.g. ``"6g"`` or ``"6H"``.

        Returns:
            The parsed :class:`ToleranceClass`.

        Raises:
            ValueError: If the designation is malformed or the position is not
                a supported ISO 965 position.
        """
        text = designation.strip()
        if len(text) < 2 or not text[:-1].isdigit():
            raise ValueError(f"Malformed tolerance class {designation!r} (expected e.g. '6g').")
        grade = int(text[:-1])
        position = text[-1]
        is_external = position.islower()
        if is_external and position not in _EXTERNAL_ES:
            raise ValueError(f"Unsupported external thread position {position!r}.")
        if not is_external and position not in _INTERNAL_EI:
            raise ValueError(f"Unsupported internal thread position {position!r}.")
        return cls(designation=text, grade=grade, position=position, is_external=is_external)

    def fundamental_deviation(self, pitch: float) -> float:
        """Return the fundamental deviation in millimetres for a given pitch.

        For external threads this is ``es`` (<= 0); for internal threads it is
        ``EI`` (>= 0).

        Args:
            pitch: Thread pitch ``P`` in millimetres.

        Returns:
            Fundamental deviation in millimetres.
        """
        if self.is_external:
            const, coeff = _EXTERNAL_ES[self.position]
            return -(const + coeff * pitch) / 1000.0
        const, coeff = _INTERNAL_EI[self.position]
        return (const + coeff * pitch) / 1000.0

    def apply(self, basic_diameter: float, pitch: float) -> float:
        """Offset a basic diameter by this class's fundamental deviation.

        Args:
            basic_diameter: The basic (nominal) diameter in millimetres.
            pitch: Thread pitch ``P`` in millimetres.

        Returns:
            The effective diameter with the fundamental deviation applied.
        """
        return basic_diameter + self.fundamental_deviation(pitch)
