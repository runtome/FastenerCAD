"""Command-line interface for FastenerCAD.

Provides three subcommands:

* ``list``     -- enumerate available parts, sizes, or materials.
* ``make``     -- generate a single standardised part and export it.
* ``assembly`` -- generate a multi-part assembly and export it.

The export format is inferred from the ``--output`` file suffix
(``.step``/``.stp``, ``.stl``, or ``.dxf``). Run ``fastenercad --help`` or
``fastenercad <command> --help`` for details.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from assemblies.anchor import AnchorBoltAssembly
from assemblies.bolt_nut import BoltNutAssembly
from assemblies.washer import WasherStack
from common.base import FastenerBase
from common.dimensions import available_sizes
from common.materials import list_materials
from standards.DIN933 import HexBoltDIN933
from standards.DIN976 import ThreadedRodDIN976
from standards.ISO4014 import HexBoltISO4014
from standards.ISO4017 import HexScrewISO4017
from standards.ISO4032 import HexNutISO4032
from standards.ISO7089 import WasherISO7089
from standards.JIS_B1180 import HexBoltJISB1180

# CLI part name -> (class, requires a --length argument).
_PARTS: dict[str, tuple[type[FastenerBase], bool]] = {
    "iso4014": (HexBoltISO4014, True),
    "iso4017": (HexScrewISO4017, True),
    "iso4032": (HexNutISO4032, False),
    "din933": (HexBoltDIN933, True),
    "jisb1180": (HexBoltJISB1180, True),
    "iso7089": (WasherISO7089, False),
    "din976": (ThreadedRodDIN976, True),
}


def _add_part_options(parser: argparse.ArgumentParser) -> None:
    """Add the thread/material/tolerance options shared by part commands."""
    parser.add_argument("--thread", choices=("cosmetic", "real"), default="cosmetic")
    parser.add_argument("--series", choices=("coarse", "fine"), default="coarse")
    parser.add_argument("--material", default=None, help="material key (see 'list materials')")
    parser.add_argument("--tolerance", default=None, help="ISO 965 class, e.g. 6g / 6H")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the CLI."""
    parser = argparse.ArgumentParser(prog="fastenercad", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    # -- list ---------------------------------------------------------------
    p_list = sub.add_parser("list", help="list available parts, sizes, or materials")
    p_list.add_argument(
        "category",
        nargs="?",
        default="all",
        choices=("parts", "sizes", "materials", "assemblies", "all"),
    )

    # -- make ---------------------------------------------------------------
    p_make = sub.add_parser("make", help="generate a single part and export it")
    p_make.add_argument("part", choices=sorted(_PARTS), help="part standard, e.g. iso4014")
    p_make.add_argument("size", help="nominal size, e.g. M8")
    p_make.add_argument("--length", type=float, default=None, help="length in mm (bolts/rods)")
    _add_part_options(p_make)
    p_make.add_argument("-o", "--output", required=True, help="output file (.step/.stl/.dxf)")
    p_make.add_argument("-q", "--quiet", action="store_true", help="suppress the summary line")

    # -- assembly -----------------------------------------------------------
    p_asm = sub.add_parser("assembly", help="generate an assembly and export it")
    p_asm.add_argument("kind", choices=("bolt-nut", "washer-stack", "anchor"))
    p_asm.add_argument("size", help="nominal size, e.g. M10")
    p_asm.add_argument("--length", type=float, default=None, help="length in mm")
    p_asm.add_argument("--clamp-length", type=float, default=None, help="grip length (bolt-nut)")
    p_asm.add_argument("--washers", action="store_true", help="include washers (bolt-nut)")
    p_asm.add_argument("--count", type=int, default=2, help="washer count (washer-stack)")
    p_asm.add_argument("--embedment", type=float, default=40.0, help="embedded length (anchor)")
    p_asm.add_argument("--thread", choices=("cosmetic", "real"), default="cosmetic")
    p_asm.add_argument("--series", choices=("coarse", "fine"), default="coarse")
    p_asm.add_argument("--material", default=None, help="material key")
    p_asm.add_argument("-o", "--output", required=True, help="output file (.step/.stl/.dxf)")
    p_asm.add_argument("-q", "--quiet", action="store_true")

    return parser


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _cmd_list(args: argparse.Namespace) -> int:
    """Handle the ``list`` command."""
    category = args.category
    if category in ("parts", "all"):
        print("Parts:")
        for name, (cls, needs_length) in sorted(_PARTS.items()):
            length = " (needs --length)" if needs_length else ""
            print(f"  {name:10s} {cls.STANDARD:10s} {cls.PART}{length}")
    if category in ("assemblies", "all"):
        print("Assemblies:")
        for name in ("bolt-nut", "washer-stack", "anchor"):
            print(f"  {name}")
    if category in ("sizes", "all"):
        print("Sizes:")
        print("  " + " ".join(available_sizes()))
    if category in ("materials", "all"):
        print("Materials:")
        print("  " + " ".join(list_materials()))
    return 0


def _build_part(args: argparse.Namespace) -> FastenerBase:
    """Construct a part instance from parsed ``make`` arguments."""
    cls, needs_length = _PARTS[args.part]
    kwargs: dict[str, object] = {
        "size": args.size,
        "thread": args.thread,
        "thread_series": args.series,
    }
    if args.material is not None:
        kwargs["material"] = args.material
    if args.tolerance is not None:
        kwargs["tolerance"] = args.tolerance
    if needs_length:
        if args.length is None:
            raise ValueError(f"part '{args.part}' requires --length")
        kwargs["length"] = args.length
    elif args.length is not None:
        raise ValueError(f"part '{args.part}' does not take --length")
    return cls(**kwargs)  # type: ignore[arg-type]


def _cmd_make(args: argparse.Namespace) -> int:
    """Handle the ``make`` command."""
    part = _build_part(args)
    out = part.save(args.output)
    if not args.quiet:
        dx, dy, dz = part.bounding_box()
        print(
            f"Wrote {out}  vol={part.volume():.1f} mm^3  "
            f"mass={part.mass():.2f} g  bbox=({dx:.1f}, {dy:.1f}, {dz:.1f})"
        )
    return 0


def _build_assembly(args: argparse.Namespace) -> BoltNutAssembly | WasherStack | AnchorBoltAssembly:
    """Construct an assembly instance from parsed ``assembly`` arguments."""
    material = {"material": args.material} if args.material is not None else {}
    if args.kind == "bolt-nut":
        if args.length is None:
            raise ValueError("assembly 'bolt-nut' requires --length")
        return BoltNutAssembly(
            size=args.size,
            length=args.length,
            clamp_length=args.clamp_length,
            washers=args.washers,
            thread=args.thread,
            thread_series=args.series,
            **material,
        )
    if args.kind == "washer-stack":
        return WasherStack(size=args.size, count=args.count, **material)
    if args.length is None:
        raise ValueError("assembly 'anchor' requires --length")
    return AnchorBoltAssembly(
        size=args.size,
        length=args.length,
        embedment=args.embedment,
        thread=args.thread,
        thread_series=args.series,
        **material,
    )


def _cmd_assembly(args: argparse.Namespace) -> int:
    """Handle the ``assembly`` command."""
    assembly = _build_assembly(args)
    out = assembly.save(args.output)
    if not args.quiet:
        dx, dy, dz = assembly.bounding_box()
        print(
            f"Wrote {out}  vol={assembly.volume():.1f} mm^3  "
            f"bbox=({dx:.1f}, {dy:.1f}, {dz:.1f})"
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code (0 on success, 2 on a handled user error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {"list": _cmd_list, "make": _cmd_make, "assembly": _cmd_assembly}
    try:
        return handlers[args.command](args)
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
