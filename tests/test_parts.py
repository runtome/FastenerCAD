"""Per-standard part geometry sanity tests (cosmetic mode)."""

from __future__ import annotations

import math

import pytest

from common.dimensions import load_entry
from standards.DIN933 import HexBoltDIN933
from standards.DIN976 import ThreadedRodDIN976
from standards.ISO4014 import HexBoltISO4014
from standards.ISO4017 import HexScrewISO4017
from standards.ISO4032 import HexNutISO4032
from standards.ISO7089 import WasherISO7089
from standards.JIS_B1180 import HexBoltJISB1180

_AC = 2.0 / math.sqrt(3.0)


def test_hex_bolt_dimensions() -> None:
    """An ISO 4014 bolt has the right height and across-corners width."""
    entry = load_entry("M8")
    bolt = HexBoltISO4014(size="M8", length=40.0)
    dx, dy, dz = bolt.bounding_box()
    assert dz == pytest.approx(40.0 + entry.hex_head.head_height, abs=1e-6)
    assert max(dx, dy) == pytest.approx(entry.hex_head.width_across_flats * _AC, abs=1e-3)
    assert bolt.volume() > 0


def test_fully_threaded_screw_shorter_than_partial() -> None:
    """A partially threaded bolt weighs more than a fully threaded one (thicker shank)."""
    partial = HexBoltISO4014(size="M8", length=40.0)
    full = HexScrewISO4017(size="M8", length=40.0)
    assert partial.volume() > full.volume()


def test_din933_matches_iso4017() -> None:
    """DIN 933 reuses ISO 4017 geometry exactly."""
    din = HexBoltDIN933(size="M10", length=30.0)
    iso = HexScrewISO4017(size="M10", length=30.0)
    assert din.volume() == pytest.approx(iso.volume(), rel=1e-9)


def test_nut_has_through_hole() -> None:
    """A nut's volume is less than the solid hex prism (it is bored through)."""
    entry = load_entry("M8")
    s, m = entry.hex_nut.width_across_flats, entry.hex_nut.height
    solid_hex_volume = (math.sqrt(3) / 2.0) * s * s * m
    nut = HexNutISO4032(size="M8")
    assert 0 < nut.volume() < solid_hex_volume
    _, _, dz = nut.bounding_box()
    assert dz == pytest.approx(m, abs=1e-6)


def test_nut_default_tolerance_is_internal() -> None:
    """Nuts default to the 6H internal tolerance class."""
    assert HexNutISO4032(size="M8").tolerance == "6H"


def test_washer_is_annular() -> None:
    """A washer's volume matches an annulus of the catalog dimensions."""
    w = load_entry("M8").washer
    expected = math.pi * ((w.outer_diameter / 2) ** 2 - (w.inner_diameter / 2) ** 2) * w.thickness
    washer = WasherISO7089(size="M8")
    assert washer.volume() == pytest.approx(expected, rel=1e-3)


def test_threaded_rod_length() -> None:
    """A threaded rod's bounding box height equals its length."""
    rod = ThreadedRodDIN976(size="M8", length=50.0)
    _, _, dz = rod.bounding_box()
    assert dz == pytest.approx(50.0, abs=1e-6)


def test_jis_width_override() -> None:
    """JIS B1180 uses a larger head width than ISO for M10."""
    jis = HexBoltJISB1180(size="M10", length=30.0)
    iso = HexBoltISO4014(size="M10", length=30.0)
    assert max(jis.bounding_box()[:2]) > max(iso.bounding_box()[:2])


def test_mass_uses_material_density() -> None:
    """Mass scales with the configured material density."""
    steel = ThreadedRodDIN976(size="M8", length=50.0, material="steel-8.8")
    alu = ThreadedRodDIN976(size="M8", length=50.0, material="aluminum")
    assert steel.mass() > alu.mass()
    assert steel.mass() == pytest.approx(steel.volume() / 1000.0 * 7.85, rel=1e-6)


def test_invalid_parameters_raise() -> None:
    """Invalid construction parameters raise clear errors."""
    with pytest.raises(ValueError):
        HexBoltISO4014(size="M8", length=-1.0)
    with pytest.raises(ValueError):
        HexBoltISO4014(size="M8", length=10.0, thread="bogus")
    with pytest.raises(KeyError):
        HexBoltISO4014(size="M8", length=10.0, material="unobtanium")
    with pytest.raises(FileNotFoundError):
        HexNutISO4032(size="M7")
