"""Generate the dimension catalog (``catalog/M*.json``).

This is a maintenance utility, not part of the runtime library. It encodes the
standardised head / nut / washer dimension tables (ISO 4014/4017, ISO 4032,
ISO 7089) and derives the thread pitch diameters from ISO 68-1 formulas and the
pitch tables in :mod:`threads.coarse` / :mod:`threads.fine`. Run it whenever the
source tables change::

    python scripts/generate_catalog.py

It uses only the standard library so it can run before ``uv sync``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from threads.coarse import COARSE_PITCH, NOMINAL_DIAMETERS  # noqa: E402
from threads.fine import fine_pitches  # noqa: E402

_CATALOG_DIR = _ROOT / "catalog"

# ISO 68-1 offset coefficients (relative to pitch P).
_D2 = 0.6495  # pitch diameter          d2 = d - 0.6495 P
_D3 = 1.2269  # bolt (external) minor    d3 = d - 1.2269 P
_D1 = 1.0825  # nut  (internal) minor    D1 = d - 1.0825 P

# Hex head: width across flats s (mm), head height k (mm) -- ISO 4014/4017.
HEX_HEAD: dict[float, tuple[float, float]] = {
    1.6: (3.2, 1.1),
    2.0: (4.0, 1.4),
    2.5: (5.0, 1.7),
    3.0: (5.5, 2.0),
    4.0: (7.0, 2.8),
    5.0: (8.0, 3.5),
    6.0: (10.0, 4.0),
    8.0: (13.0, 5.3),
    10.0: (16.0, 6.4),
    12.0: (18.0, 7.5),
    16.0: (24.0, 10.0),
    20.0: (30.0, 12.5),
    24.0: (36.0, 15.0),
    30.0: (46.0, 18.7),
    36.0: (55.0, 22.5),
    42.0: (65.0, 26.0),
    48.0: (75.0, 30.0),
    56.0: (85.0, 35.0),
    64.0: (95.0, 40.0),
}

# Hex nut (ISO 4032, style 1): width across flats s (mm), height m (mm).
HEX_NUT: dict[float, tuple[float, float]] = {
    1.6: (3.2, 1.3),
    2.0: (4.0, 1.6),
    2.5: (5.0, 2.0),
    3.0: (5.5, 2.4),
    4.0: (7.0, 3.2),
    5.0: (8.0, 4.7),
    6.0: (10.0, 5.2),
    8.0: (13.0, 6.8),
    10.0: (16.0, 8.4),
    12.0: (18.0, 10.8),
    16.0: (24.0, 14.8),
    20.0: (30.0, 18.0),
    24.0: (36.0, 21.5),
    30.0: (46.0, 25.6),
    36.0: (55.0, 31.0),
    42.0: (65.0, 34.0),
    48.0: (75.0, 38.0),
    56.0: (85.0, 45.0),
    64.0: (95.0, 51.0),
}

# Plain washer (ISO 7089, 200 HV): inner d1, outer d2, thickness h (mm).
WASHER: dict[float, tuple[float, float, float]] = {
    1.6: (1.7, 4.0, 0.3),
    2.0: (2.2, 5.0, 0.3),
    2.5: (2.7, 6.0, 0.5),
    3.0: (3.2, 7.0, 0.5),
    4.0: (4.3, 9.0, 0.8),
    5.0: (5.3, 10.0, 1.0),
    6.0: (6.4, 12.0, 1.6),
    8.0: (8.4, 16.0, 1.6),
    10.0: (10.5, 20.0, 2.0),
    12.0: (13.0, 24.0, 2.5),
    16.0: (17.0, 30.0, 3.0),
    20.0: (21.0, 37.0, 3.0),
    24.0: (25.0, 44.0, 4.0),
    30.0: (31.0, 56.0, 4.0),
    36.0: (37.0, 66.0, 5.0),
    42.0: (45.0, 78.0, 8.0),
    48.0: (52.0, 92.0, 8.0),
    56.0: (62.0, 105.0, 10.0),
    64.0: (70.0, 115.0, 10.0),
}


def _designation(diameter: float) -> str:
    """Return the size designation, dropping a trailing ``.0`` (e.g. ``M8``)."""
    if diameter.is_integer():
        return f"M{int(diameter)}"
    return f"M{diameter}"


def _thread_block(diameter: float, pitch: float, series: str) -> dict[str, float]:
    """Compute one thread sub-block from a diameter and pitch (ISO 68-1)."""
    return {
        "pitch": round(pitch, 4),
        "pitch_dia": round(diameter - _D2 * pitch, 4),
        "minor_dia_bolt": round(diameter - _D3 * pitch, 4),
        "minor_dia_nut": round(diameter - _D1 * pitch, 4),
    }


def build_entry(diameter: float) -> dict[str, object]:
    """Build the full catalog dict for one nominal diameter."""
    head_s, head_k = HEX_HEAD[diameter]
    nut_s, nut_m = HEX_NUT[diameter]
    w_id, w_od, w_h = WASHER[diameter]
    return {
        "designation": _designation(diameter),
        "nominal_diameter": diameter,
        "thread": {
            "coarse": _thread_block(diameter, COARSE_PITCH[diameter], "coarse"),
            "fine": [_thread_block(diameter, p, "fine") for p in fine_pitches(diameter)],
        },
        "hex_head": {"width_across_flats": head_s, "head_height": head_k},
        "hex_nut": {"width_across_flats": nut_s, "height": nut_m},
        "washer": {"inner_dia": w_id, "outer_dia": w_od, "thickness": w_h},
    }


def main() -> None:
    """Generate and write every catalog JSON file."""
    _CATALOG_DIR.mkdir(exist_ok=True)
    for diameter in NOMINAL_DIAMETERS:
        entry = build_entry(diameter)
        path = _CATALOG_DIR / f"{entry['designation']}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(entry, fh, indent=2)
            fh.write("\n")
        print(f"wrote {path.relative_to(_ROOT)}")
    print(f"done: {len(NOMINAL_DIAMETERS)} sizes")


if __name__ == "__main__":
    main()
