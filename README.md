# FastenerCAD

**Production-quality, parametric CAD library for mechanical fasteners.**

FastenerCAD generates ISO, DIN, and JIS standard fasteners as parametric 3D solids
using [CADQuery](https://cadquery.readthedocs.io/) and exports them to **STEP**, **STL**,
and **DXF**. It is modular, object-oriented, and fully data-driven: every dimension comes
from JSON catalog files, never from hardcoded values in geometry code.

---

## Features

- **Parts:** hex bolt, hex screw (fully threaded), hex nut, plain washer, threaded rod.
- **Assemblies:** bolt + washer(s) + nut, washered joints, anchor bolts.
- **Threads:** metric coarse **and** fine, per ISO 68-1 / ISO 261.
  - `thread="cosmetic"` *(default)* — plain cylinder at pitch diameter with a lead-in
    chamfer. Fast, robust STEP/STL export, small files.
  - `thread="real"` — true swept helical thread. Geometrically accurate, slower, heavier.
- **Standards:** ISO 4014, ISO 4017, ISO 4032, DIN 933, JIS B1180, ISO 7089, DIN 976.
- **Full ISO metric range:** M1.6 through M64.
- **Export:** STEP (`.step`), STL (`.stl`), DXF (`.dxf`).
- Fully type-hinted, `black`/`ruff`/`mypy`-clean, tested with `pytest`.

## Standards coverage

| Standard   | Part                              | Class                 |
|------------|-----------------------------------|-----------------------|
| ISO 4014   | Hex head bolt (partially threaded)| `HexBoltISO4014`      |
| ISO 4017   | Hex head screw (fully threaded)   | `HexScrewISO4017`     |
| ISO 4032   | Hex nut, style 1                  | `HexNutISO4032`       |
| DIN 933    | Hex bolt (fully threaded)         | `HexBoltDIN933`       |
| JIS B1180  | Hex bolt / screw                  | `HexBoltJISB1180`     |
| ISO 7089   | Plain washer                      | `WasherISO7089`       |
| DIN 976    | Threaded rod / studding           | `ThreadedRodDIN976`   |

## Installation

FastenerCAD uses [`uv`](https://docs.astral.sh/uv/) and targets **Python 3.12**
(required by the CADQuery/OCP wheels).

```bash
uv sync           # create .venv and install runtime + dev dependencies
```

## Quickstart

```python
from standards.ISO4014 import HexBoltISO4014
from standards.ISO4032 import HexNutISO4032

# A partially threaded M8 hex bolt, 40 mm long, coarse thread (default).
bolt = HexBoltISO4014(size="M8", length=40.0)
bolt.to_step("M8x40_bolt.step")
bolt.to_stl("M8x40_bolt.stl")

# Matching hex nut with a true helical thread.
nut = HexNutISO4032(size="M8", thread="real")
nut.to_step("M8_nut.step")

print(f"Bolt mass: {bolt.mass():.2f} g")   # uses material density
```

Assemblies:

```python
from assemblies.bolt_nut import BoltNutAssembly

joint = BoltNutAssembly(size="M10", length=50.0, clamp_length=30.0, washers=True)
joint.to_step("M10_joint.step")
```

## Command line

Installing the package provides a `fastenercad` command (or run `python -m cli`).
The export format is inferred from the output file suffix.

```bash
# Discover what is available
fastenercad list                      # parts, assemblies, sizes, materials
fastenercad list materials

# Generate a part (format from the -o suffix: .step / .stl / .dxf)
fastenercad make iso4014 M8 --length 40 -o bolt.step
fastenercad make iso4032 M8 --thread real -o nut.stl
fastenercad make din976 M10 --length 60 --series fine -o rod.step

# Generate an assembly
fastenercad assembly bolt-nut M10 --length 50 --washers -o joint.step
fastenercad assembly washer-stack M8 --count 4 -o shims.step
fastenercad assembly anchor M12 --length 120 --embedment 40 -o anchor.step
```

Common `make` options: `--thread {cosmetic,real}`, `--series {coarse,fine}`,
`--material`, `--tolerance`, `--length` (bolts/screws/rods).

## Project layout

```
common/      base class, dimension dataclasses + catalog loader, materials, tolerances, utils
threads/     ISO 68-1 metric thread profile + coarse/fine pitch tables (cosmetic + real)
standards/   one module per standard (ISO4014, ISO4017, ISO4032, DIN933, JIS_B1180, ...)
assemblies/  multi-part models (bolt+nut, washer stacks, anchors)
cli/          the `fastenercad` command-line interface
export/       STEP / STL / DXF writers
catalog/     one JSON file per size (M1.6 ... M64) — all dimensions live here
tests/        pytest suite
examples/     runnable generation + export scripts
```

## Development

```bash
uv run pytest            # run the test suite
uv run ruff check .      # lint
uv run black --check .   # formatting
uv run mypy .            # static type check
```

## Design principles

- **Data ≠ geometry.** Dimensions live in `catalog/*.json`; geometry code reads typed
  dataclasses and contains no dimension literals.
- **One base class.** Every part inherits `FastenerBase`, which owns model caching,
  export delegation, and mass/volume/bounding-box computation.
- **Shared thread engine.** Cosmetic and real threads come from a single profile module,
  reused by every part (composition over duplication).
- **SOLID / PEP 8.** No global state; small, reusable helpers; strict typing.

## License

MIT — see `LICENSE`.
