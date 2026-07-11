"""Generate a sample of every part and assembly, exporting STEP/STL/DXF.

Run with::

    uv run python examples/generate_all.py

Outputs are written to ``examples/output/``.
"""

from __future__ import annotations

from pathlib import Path

from assemblies.bolt_nut import BoltNutAssembly
from common.base import FastenerBase
from standards.DIN976 import ThreadedRodDIN976
from standards.ISO4014 import HexBoltISO4014
from standards.ISO4017 import HexScrewISO4017
from standards.ISO4032 import HexNutISO4032
from standards.ISO7089 import WasherISO7089

_OUTPUT = Path(__file__).resolve().parent / "output"


def _export_part(part: FastenerBase, stem: str) -> None:
    """Export a single part to STEP, STL, and DXF and print a summary."""
    part.to_step(_OUTPUT / f"{stem}.step")
    part.to_stl(_OUTPUT / f"{stem}.stl")
    part.to_dxf(_OUTPUT / f"{stem}.dxf")
    dx, dy, dz = part.bounding_box()
    print(f"{stem:24s} vol={part.volume():9.1f} mm^3  bbox=({dx:.1f},{dy:.1f},{dz:.1f})")


def main() -> None:
    """Generate and export the sample parts and one assembly."""
    _OUTPUT.mkdir(parents=True, exist_ok=True)

    _export_part(HexBoltISO4014(size="M8", length=40.0), "iso4014_hex_bolt_M8x40")
    _export_part(HexScrewISO4017(size="M8", length=20.0), "iso4017_hex_screw_M8x20")
    _export_part(HexNutISO4032(size="M8"), "iso4032_hex_nut_M8")
    _export_part(WasherISO7089(size="M8"), "iso7089_washer_M8")
    _export_part(ThreadedRodDIN976(size="M8", length=60.0), "din976_threaded_rod_M8x60")

    joint = BoltNutAssembly(size="M10", length=50.0, clamp_length=30.0, washers=True)
    joint.to_step(_OUTPUT / "assembly_bolt_nut_M10.step")
    dx, dy, dz = joint.bounding_box()
    name = "assembly_bolt_nut_M10"
    print(f"{name:24s} vol={joint.volume():9.1f} mm^3  bbox=({dx:.1f},{dy:.1f},{dz:.1f})")

    print(f"\nWrote outputs to {_OUTPUT}")


if __name__ == "__main__":
    main()
