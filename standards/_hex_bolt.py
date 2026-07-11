"""Shared hex-bolt geometry, reused by every hex bolt/screw standard.

:class:`HexBoltBase` assembles a hex bolt from three pieces -- a threaded tip
section, an optional plain shank, and a chamfered hex head -- using only the
catalog dimensions and the shared :class:`~threads.ThreadProfile` engine. Each
concrete standard overrides small hooks (thread length, head width) rather than
re-implementing the geometry, so there is no duplicated modelling code.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

import cadquery as cq

from common.base import FastenerBase
from common.utils import chamfer_hex_head, hex_prism, require_positive
from threads import ThreadProfile

# Tolerance below which the plain shank is considered absent (fully threaded).
_EPS = 1e-9


@dataclass
class HexBoltBase(FastenerBase):
    """Abstract base for hex bolts and screws.

    The bolt is modelled tip-down: the threaded tip starts at ``z = 0``, the
    bearing face is at ``z = length``, and the chamfered head occupies
    ``length <= z <= length + k``.

    Attributes:
        length: Shank length ``l`` measured from under the head to the tip (mm).
    """

    length: float

    def __post_init__(self) -> None:
        """Validate shared parameters plus the bolt length."""
        super().__post_init__()
        require_positive(self.length, "length")

    # -- Overridable hooks --------------------------------------------------

    def _head_width_across_flats(self) -> float:
        """Return the head width across flats ``s`` (mm)."""
        return self.entry.hex_head.width_across_flats

    def _head_height(self) -> float:
        """Return the head height ``k`` (mm)."""
        return self.entry.hex_head.head_height

    @abstractmethod
    def _thread_length(self) -> float:
        """Return the threaded length ``b`` measured from the tip (mm)."""
        raise NotImplementedError

    def _thread_profile(self) -> ThreadProfile:
        """Return the thread engine bound to this bolt's size/series/mode."""
        return ThreadProfile.from_size(self.size, self.thread_series, mode=self.thread)

    # -- Geometry -----------------------------------------------------------

    def _build(self) -> cq.Workplane:
        """Build the hex bolt solid (threaded tip + shank + chamfered head)."""
        diameter = self.entry.nominal_diameter
        width_across_flats = self._head_width_across_flats()
        head_height = self._head_height()
        length = self.length
        thread_length = min(self._thread_length(), length)

        # Threaded tip section, with the lead-in chamfer at the free tip (z = 0).
        result = self._thread_profile().external_shaft(
            thread_length, chamfer_tip=False, chamfer_start=True
        )

        # Plain shank at nominal diameter between the thread and the head.
        if thread_length < length - _EPS:
            shank = (
                cq.Workplane("XY")
                .circle(diameter / 2.0)
                .extrude(length - thread_length)
                .translate((0.0, 0.0, thread_length))
            )
            result = result.union(shank)

        # Chamfered hex head, bearing face flush with the shank at z = length.
        head = chamfer_hex_head(
            hex_prism(width_across_flats, head_height), width_across_flats, head_height
        ).translate((0.0, 0.0, length))
        return result.union(head)
