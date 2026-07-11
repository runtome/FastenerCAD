"""Real (helical) thread build tests.

These are slower than cosmetic-mode tests, so they are marked ``slow`` and
restricted to small sizes. Run just these with ``pytest -m slow``; skip them with
``pytest -m 'not slow'``.
"""

from __future__ import annotations

import pytest

from standards.DIN976 import ThreadedRodDIN976
from standards.ISO4032 import HexNutISO4032

pytestmark = pytest.mark.slow


def test_real_rod_is_valid_solid() -> None:
    """A real-thread rod builds to a single valid solid within its length."""
    rod = ThreadedRodDIN976(size="M8", length=20.0, thread="real")
    solids = rod.model.solids().vals()
    assert len(solids) == 1
    assert rod.volume() > 0
    _, _, dz = rod.bounding_box()
    assert dz == pytest.approx(20.0, abs=1e-6)


def test_real_nut_is_valid_solid() -> None:
    """A real-thread nut builds to a valid, positive-volume solid."""
    nut = HexNutISO4032(size="M8", thread="real")
    assert nut.volume() > 0
    _, _, dz = nut.bounding_box()
    assert dz == pytest.approx(load_height("M8"), abs=1e-6)


def load_height(size: str) -> float:
    """Return the nut height for a size (helper)."""
    from common.dimensions import load_entry

    return load_entry(size).hex_nut.height
