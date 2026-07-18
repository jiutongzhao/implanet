"""Camera-distance (perspective) demo — the orthographic → close-up ladder.

`render_disk` / `plot_disk` take an optional ``distance`` (planet radii,
> 1). ``None`` is the orthographic view (camera at infinity, unchanged);
a finite value switches on a perspective projection. Framing is
*silhouette-normalized*, so the apparent disk always fills ``[-1, +1]`` —
what changes as the camera closes in is the visible surface: the cap
shrinks to angular radius ``arccos(1/distance)`` and foreshortens toward
the limb.

Two outputs (committed under ``figures/perspective/``):

* ``<body>_ladder.png`` — one matplotlib figure, four panels
  (orthographic, then a few distances) via ``plot_disk`` with the
  graticule + terminator overlays, so you can see the vector layers stay
  registered with the raster under perspective.
* ``<body>_dist_<d>.png`` — the raw ``render_disk`` RGBA disks (no
  overlays) at each distance, ready to drop onto any background.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from implanet import plot_disk, render_disk
from implanet.assets import get_texture

OUT_DIR = Path(__file__).resolve().parent.parent / "figures" / "perspective"

# None = orthographic (∞); the rest are camera distances in planet radii.
DISTANCES = [None, 6.0, 3.0, 1.8]
SUN = (1.0, 0.35, 0.45)          # sub-solar off to one side → clear terminator
VIEW = "yz"                      # prime-meridian equator view
MAX_TEX = 4096                   # downsample huge source maps (memory)


def _label(d) -> str:
    return "orthographic (∞)" if d is None else f"distance = {d:g} R"


def _tag(d) -> str:
    return "inf" if d is None else f"{d:g}".replace(".", "p")


def _load(body: str, max_tex: int) -> Image.Image:
    im = Image.open(get_texture(body)).convert("RGB")
    if max(im.size) > max_tex:
        im.thumbnail((max_tex, max_tex))             # keeps 2:1, bounds RAM
    return im


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--body", default="Earth")
    ap.add_argument("--size", type=int, default=768)
    ap.add_argument("--max-tex", type=int, default=MAX_TEX)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        tex = _load(args.body, args.max_tex)
    except Exception as exc:                          # manual-only / offline
        print(f"cannot load {args.body}: {exc}", file=sys.stderr)
        return 1

    # --- composite ladder with overlays -------------------------------
    fig, axes = plt.subplots(1, len(DISTANCES),
                             figsize=(3.2 * len(DISTANCES), 3.4))
    for ax, d in zip(np.atleast_1d(axes), DISTANCES):
        plot_disk(tex, view_direction=VIEW, sun_direction=SUN,
                  distance=d, size=args.size, ax=ax, style_axes=True)
        ax.set_title(_label(d), fontsize=11)
    fig.suptitle(f"{args.body} — camera distance ladder "
                 f"(silhouette-normalized perspective)", fontsize=12)
    fig.tight_layout()
    ladder = OUT_DIR / f"{args.body.lower()}_ladder.png"
    fig.savefig(ladder, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {ladder.name}")

    # --- raw transparent disks (no overlays) --------------------------
    for d in DISTANCES:
        img = render_disk(tex, view_direction=VIEW, sun_direction=SUN,
                          distance=d, size=args.size, margin=1.0)
        dest = OUT_DIR / f"{args.body.lower()}_dist_{_tag(d)}.png"
        Image.fromarray(img, "RGBA").save(dest, optimize=True)
        print(f"wrote {dest.name}")

    print(f"\n-> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
