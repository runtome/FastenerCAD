"""Thread profile math and ThreadProfile factory tests."""

from __future__ import annotations

import math

import pytest

from common.utils import as_shape
from threads import ThreadProfile, metric
from threads.coarse import coarse_pitch
from threads.fine import primary_fine_pitch


def test_fundamental_height() -> None:
    """H = P * sqrt(3) / 2."""
    assert metric.fundamental_height(1.0) == pytest.approx(math.sqrt(3) / 2)


def test_profile_diameters() -> None:
    """Pitch and minor diameters follow ISO 68-1 for M8 (P = 1.25)."""
    d, p = 8.0, 1.25
    assert metric.basic_pitch_diameter(d, p) == pytest.approx(8.0 - 0.6495 * p)
    assert metric.bolt_minor_diameter(d, p) == pytest.approx(8.0 - 1.2269 * p)
    assert metric.nut_minor_diameter(d, p) == pytest.approx(8.0 - 1.0825 * p)


def test_pitch_tables() -> None:
    """Coarse and fine pitch lookups return the standard values."""
    assert coarse_pitch(8.0) == pytest.approx(1.25)
    assert primary_fine_pitch(8.0) == pytest.approx(1.0)


def test_thread_profile_from_size() -> None:
    """ThreadProfile.from_size binds the correct catalog dimensions."""
    profile = ThreadProfile.from_size("M8", series="coarse")
    assert profile.dimensions.pitch == pytest.approx(1.25)
    assert profile.mode == "cosmetic"


def test_cosmetic_external_shaft_diameter() -> None:
    """A cosmetic external shaft is a cylinder at the pitch diameter."""
    profile = ThreadProfile.from_size("M8", series="coarse", mode="cosmetic")
    shaft = profile.external_shaft(20.0, chamfer_tip=False, chamfer_start=False)
    bb = as_shape(shaft).BoundingBox()
    assert bb.xlen == pytest.approx(profile.dimensions.pitch_diameter, abs=1e-6)
    assert bb.zlen == pytest.approx(20.0, abs=1e-6)
