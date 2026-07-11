"""Catalog integrity and dimension-record tests."""

from __future__ import annotations

import math

import pytest

from common.dimensions import available_sizes, load_entry
from threads.coarse import COARSE_PITCH


def test_all_sizes_present() -> None:
    """Every coarse-table diameter has a catalog entry."""
    sizes = available_sizes()
    assert len(sizes) == len(COARSE_PITCH)
    assert "M6" in sizes
    assert "M1.6" in sizes
    assert "M64" in sizes


@pytest.mark.parametrize("size", available_sizes())
def test_entry_fields_positive(size: str) -> None:
    """All dimensions in every entry are strictly positive."""
    entry = load_entry(size)
    assert entry.nominal_diameter > 0
    for thread in (entry.thread_coarse, *entry.thread_fine):
        assert thread.pitch > 0
        assert thread.pitch_diameter > 0
        assert 0 < thread.minor_diameter_bolt < thread.pitch_diameter < thread.nominal_diameter
        assert thread.minor_diameter_bolt < thread.minor_diameter_nut < thread.nominal_diameter
    assert entry.hex_head.width_across_flats > entry.nominal_diameter
    assert entry.hex_head.head_height > 0
    assert entry.hex_nut.height > 0
    assert entry.washer.outer_diameter > entry.washer.inner_diameter > 0
    assert entry.washer.thickness > 0


@pytest.mark.parametrize("size", available_sizes())
def test_thread_math_matches_iso(size: str) -> None:
    """Catalog thread diameters follow the ISO 68-1 formulas."""
    entry = load_entry(size)
    d = entry.nominal_diameter
    t = entry.thread_coarse
    assert t.pitch_diameter == pytest.approx(d - 0.6495 * t.pitch, abs=1e-3)
    assert t.minor_diameter_bolt == pytest.approx(d - 1.2269 * t.pitch, abs=1e-3)
    assert t.minor_diameter_nut == pytest.approx(d - 1.0825 * t.pitch, abs=1e-3)


def test_across_corners_derivation() -> None:
    """Width across corners is s * 2 / sqrt(3)."""
    head = load_entry("M6").hex_head
    assert head.width_across_corners == pytest.approx(head.width_across_flats * 2 / math.sqrt(3))


def test_fine_series_selection() -> None:
    """Fine-series lookup returns the requested pitch."""
    entry = load_entry("M10")
    assert entry.thread("fine").pitch == pytest.approx(1.25)  # preferred fine
    assert entry.thread("fine", pitch=0.75).pitch == pytest.approx(0.75)
    with pytest.raises(ValueError):
        entry.thread("fine", pitch=0.5)


def test_unknown_size_raises() -> None:
    """Loading a missing size raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_entry("M7")
