"""Assembly build and export tests (cosmetic mode)."""

from __future__ import annotations

from pathlib import Path

import pytest

from assemblies.anchor import AnchorBoltAssembly
from assemblies.bolt_nut import BoltNutAssembly
from assemblies.washer import WasherStack


def test_bolt_nut_builds_and_exports(tmp_path: Path) -> None:
    """A bolt+nut+washers assembly builds and exports to STEP."""
    joint = BoltNutAssembly(size="M10", length=50.0, clamp_length=30.0, washers=True)
    assert joint.volume() > 0
    assert joint.bounding_box()[2] > 50.0  # includes the head above the shank
    out = joint.to_step(tmp_path / "joint.step")
    assert out.is_file() and out.stat().st_size > 0


def test_bolt_nut_clamp_too_long_raises() -> None:
    """An over-long clamp length is rejected."""
    with pytest.raises(ValueError):
        BoltNutAssembly(size="M8", length=20.0, clamp_length=25.0).volume()


def test_washer_stack() -> None:
    """A washer stack's height is count * thickness."""
    from common.dimensions import load_entry

    thickness = load_entry("M8").washer.thickness
    stack = WasherStack(size="M8", count=3)
    assert stack.bounding_box()[2] == pytest.approx(3 * thickness, abs=1e-6)


def test_anchor_builds() -> None:
    """An anchor-bolt assembly builds with positive volume."""
    anchor = AnchorBoltAssembly(size="M12", length=120.0, embedment=40.0)
    assert anchor.volume() > 0
