"""Export round-trip tests for STEP, STL, and DXF."""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
import pytest

from common.utils import as_shape
from standards.ISO4014 import HexBoltISO4014
from standards.ISO4032 import HexNutISO4032


def test_step_export_and_reimport(tmp_path: Path) -> None:
    """A STEP export is non-empty and re-imports to a positive-volume solid."""
    bolt = HexBoltISO4014(size="M6", length=20.0)
    out = bolt.to_step(tmp_path / "bolt.step")
    assert out.is_file() and out.stat().st_size > 0

    reimported = cq.importers.importStep(str(out))
    assert as_shape(reimported).Volume() == pytest.approx(bolt.volume(), rel=1e-3)


def test_stl_export(tmp_path: Path) -> None:
    """An STL export writes a non-empty file."""
    out = HexNutISO4032(size="M6").to_stl(tmp_path / "nut.stl")
    assert out.is_file() and out.stat().st_size > 0


def test_dxf_export(tmp_path: Path) -> None:
    """A DXF export writes a non-empty file."""
    out = HexNutISO4032(size="M6").to_dxf(tmp_path / "nut.dxf")
    assert out.is_file() and out.stat().st_size > 0


def test_save_dispatch_by_suffix(tmp_path: Path) -> None:
    """save() picks the exporter from the file suffix."""
    bolt = HexBoltISO4014(size="M6", length=20.0)
    assert bolt.save(tmp_path / "b.step").is_file()
    assert bolt.save(tmp_path / "b.stl").is_file()
    with pytest.raises(ValueError):
        bolt.save(tmp_path / "b.obj")
