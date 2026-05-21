"""Fully sunlit Earth at a given instant ("Blue Marble" geometry).

The camera sits on the Sun->Earth line looking at the sub-solar
hemisphere (``view_direction = -sun_direction``), so the terminator
falls on the limb and the whole visible disk is lit. Both vectors come
from SPICE, so the continent under the Sun is correct for the timestamp.

Output: examples/figures/earth_dayside_20260403_002739.png
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

from implanet import render_disk
from implanet.assets import get_texture

UTC = "2026-04-03T00:27:39"
OUT = (Path(__file__).resolve().parent / "figures"
       / "earth_dayside_20260403_002739.png")


def main() -> int:
    try:
        from implanet import sun_direction, sub_solar_point
    except ImportError:
        print("Needs the optional `spiceypy` dependency: "
              "pip install -e .[all]", file=sys.stderr)
        return 1

    try:
        sun = sun_direction("Earth", UTC)
        ss_lat, ss_lon = sub_solar_point("Earth", UTC)
    except Exception as exc:
        print(f"SPICE lookup failed ({exc}); run "
              "`python -c 'from implanet import ensure_kernels; "
              "ensure_kernels()'` first.", file=sys.stderr)
        return 1

    view = tuple(-float(c) for c in sun)        # sub-observer == sub-solar
    # RGBA texture → render_disk leaves off-disk pixels transparent
    # (alpha=0), so the saved PNG drops onto any page background. Use a
    # black background colour so the transparent pixels are (0,0,0,0):
    # a white transparent fill bleeds a bright halo at the limb when the
    # PNG is downscaled, black does not.
    img = render_disk(
        Image.open(get_texture("Earth")).convert("RGBA"),
        view_direction=view,
        sun_direction=sun,
        ambient=0.04,
        size=1024,
        margin=1.06,
        background=(0, 0, 0),
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, "RGBA").save(OUT)
    print(f"wrote {OUT}  (sub-solar {ss_lat:+.2f}°, {ss_lon:+.2f}°E, "
          f"{UTC} UTC)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
