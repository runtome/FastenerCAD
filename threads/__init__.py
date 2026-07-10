"""Thread engine package: profile math, pitch tables, and the ThreadProfile factory.

CADQuery-dependent imports are deferred (annotations only / inside methods) so
that the pure-data pitch tables can be imported without CADQuery installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from threads.coarse import COARSE_PITCH, coarse_pitch
from threads.fine import FINE_PITCHES, fine_pitches, primary_fine_pitch

if TYPE_CHECKING:
    import cadquery as cq

    from common.dimensions import ThreadDimensions


@dataclass(frozen=True, slots=True)
class ThreadProfile:
    """A thread bound to concrete dimensions plus a build mode and hand.

    This is the single object the geometry code uses to build threads, so parts
    never call the low-level :mod:`threads.metric` builders directly.

    Attributes:
        dimensions: The thread dimensions (from the catalog).
        mode: ``"cosmetic"`` (default) or ``"real"``.
        lefthand: ``True`` for a left-hand thread.
    """

    dimensions: ThreadDimensions
    mode: str = "cosmetic"
    lefthand: bool = False

    @classmethod
    def from_size(
        cls,
        size: str,
        series: str = "coarse",
        pitch: float | None = None,
        mode: str = "cosmetic",
        lefthand: bool = False,
    ) -> ThreadProfile:
        """Create a :class:`ThreadProfile` from a catalog size.

        Args:
            size: Size designation, e.g. ``"M8"``.
            series: ``"coarse"`` or ``"fine"``.
            pitch: Exact fine pitch to select when several exist.
            mode: ``"cosmetic"`` or ``"real"``.
            lefthand: Build a left-hand thread.

        Returns:
            The configured :class:`ThreadProfile`.
        """
        from common.dimensions import load_entry

        dims = load_entry(size).thread(series, pitch)
        return cls(dimensions=dims, mode=mode, lefthand=lefthand)

    def external_shaft(
        self,
        length: float,
        chamfer_tip: bool = True,
        chamfer_start: bool = False,
    ) -> cq.Workplane:
        """Build an externally threaded cylinder of the given length (+Z)."""
        from threads import metric

        return metric.external_shaft(
            self.dimensions,
            length,
            mode=self.mode,
            chamfer_tip=chamfer_tip,
            chamfer_start=chamfer_start,
            lefthand=self.lefthand,
        )

    def internal_cut(self, length: float) -> cq.Workplane:
        """Build the negative solid that forms a tapped hole of the given depth."""
        from threads import metric

        return metric.internal_thread_cut(
            self.dimensions, length, mode=self.mode, lefthand=self.lefthand
        )


__all__ = [
    "COARSE_PITCH",
    "FINE_PITCHES",
    "ThreadProfile",
    "coarse_pitch",
    "fine_pitches",
    "primary_fine_pitch",
]
