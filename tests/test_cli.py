"""CLI tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli import main


def test_list_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """`list` prints parts, sizes, and materials."""
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "iso4014" in out
    assert "M8" in out
    assert "steel-8.8" in out


def test_make_part_exports(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`make` builds a part and writes the requested format."""
    out = tmp_path / "bolt.step"
    assert main(["make", "iso4014", "M8", "--length", "40", "-o", str(out)]) == 0
    assert out.is_file() and out.stat().st_size > 0
    assert "vol=" in capsys.readouterr().out


def test_make_nut_without_length(tmp_path: Path) -> None:
    """A nut needs no length and exports to STL."""
    out = tmp_path / "nut.stl"
    assert main(["make", "iso4032", "M8", "-o", str(out)]) == 0
    assert out.is_file()


def test_make_missing_length_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A bolt without --length returns an error exit code."""
    rc = main(["make", "iso4014", "M8", "-o", str(tmp_path / "x.step")])
    assert rc == 2
    assert "requires --length" in capsys.readouterr().err


def test_make_unknown_size_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An unknown size returns an error exit code."""
    rc = main(["make", "iso4032", "M7", "-o", str(tmp_path / "x.step")])
    assert rc == 2
    assert "error:" in capsys.readouterr().err


def test_assembly_exports(tmp_path: Path) -> None:
    """`assembly bolt-nut` builds and exports."""
    out = tmp_path / "joint.step"
    rc = main(["assembly", "bolt-nut", "M10", "--length", "50", "--washers", "-o", str(out)])
    assert rc == 0
    assert out.is_file() and out.stat().st_size > 0


def test_bad_output_suffix_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An unsupported output suffix returns an error exit code."""
    rc = main(["make", "iso4032", "M8", "-o", str(tmp_path / "x.obj")])
    assert rc == 2
    assert "Unsupported export suffix" in capsys.readouterr().err
