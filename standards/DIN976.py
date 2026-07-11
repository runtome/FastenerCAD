"""DIN 976 -- Metal threaded rods / studding (fully threaded studs)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import cadquery as cq

from common.base import FastenerBase
from common.utils import require_positive
from threads import ThreadProfile


@dataclass
class ThreadedRodDIN976(FastenerBase):
    """A DIN 976 fully threaded rod, chamfered at both ends.

    Attributes:
        length: Overall rod length (mm).
    """

    length: float

    STANDARD: ClassVar[str] = "DIN 976"
    PART: ClassVar[str] = "threaded rod"

    def __post_init__(self) -> None:
        """Validate shared parameters plus the rod length."""
        super().__post_init__()
        require_positive(self.length, "length")

    def _build(self) -> cq.Workplane:
        """Build the threaded rod solid (full-length external thread)."""
        thread = ThreadProfile.from_size(self.size, self.thread_series, mode=self.thread)
        return thread.external_shaft(self.length, chamfer_tip=True, chamfer_start=True)
