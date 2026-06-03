"""Regenerate the full implanet publication figure series.

Runs every ``figNN_*.py`` plate in order and writes
``figures/nature/figNN_*.{png,pdf,svg}``. The ``.png`` files are light
previews (committed); the ``.pdf``/``.svg`` masters keep text editable
for figure assembly and are regeneratable from these scripts.

    python examples/nature/make_all.py
"""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))   # so each plate can `import _style`

PLATES = [
    "fig01_frame_and_projection",
    "fig02_viewing_geometry",
    "fig03_illumination",
    "fig04_earth_spice",
    "fig05_texture_gallery",
    "fig06_variant_comparison",
]


def main() -> int:
    failures = []
    for name in PLATES:
        print(f"── {name} " + "─" * (40 - len(name)))
        t0 = time.time()
        try:
            mod = importlib.import_module(name)
            rc = mod.main()
            if isinstance(rc, int) and rc != 0:
                failures.append((name, f"returned {rc}"))
        except Exception as exc:  # noqa: BLE001
            failures.append((name, repr(exc)))
            print(f"  FAILED: {exc!r}", file=sys.stderr)
        else:
            print(f"  ({time.time() - t0:.1f}s)")

    print("\n" + "=" * 52)
    if failures:
        for name, why in failures:
            print(f"  ✗ {name}: {why}")
        return 1
    print(f"  ✓ {len(PLATES)} plates written to figures/nature/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
