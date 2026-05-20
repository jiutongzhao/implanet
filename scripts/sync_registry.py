"""Copy the authoritative registries into the package so wheels ship them.

The editable source of truth is ``maps/manifest.json`` and
``maps/kernels.json`` at the repo root. The installed package can't see
the repo, so it falls back to packaged copies under
``implanet/assets/data/``. Run this whenever you edit either registry
(``tests/test_assets.py`` fails if they drift).
"""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "maps"
DST = REPO / "implanet" / "assets" / "data"
FILES = ["manifest.json", "kernels.json"]


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    changed = []
    for name in FILES:
        src, dst = SRC / name, DST / name
        if not src.is_file():
            print(f"  ! missing source {src}", file=sys.stderr)
            return 1
        if not dst.is_file() or not filecmp.cmp(src, dst, shallow=False):
            shutil.copyfile(src, dst)
            changed.append(name)
    if changed:
        print(f"  synced: {', '.join(changed)} -> {DST}")
    else:
        print("  registries already in sync")

    # Always refresh ATTRIBUTION.md too — it's derived from the same
    # registries, and tests assert it stays current.
    from build_attribution import main as build_attribution
    rc = build_attribution()
    if rc != 0:
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
