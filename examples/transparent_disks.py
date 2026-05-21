"""Export every body's disk as a transparent PNG on an exact [-1, 1] grid,
from three viewpoints, plus contact sheets that prove the transparency.

Three sub-observer geometries per body:

* **equator** — sub-observer at (lat 0, lon 0)        [the original view]
* **north**   — looking straight down the north pole  (lat +90)
* **south**   — looking straight down the south pole   (lat -90)

For *every* planet / satellite in the registry (its default texture):

* **Transparent off the disk** — RGBA, off-disk ``alpha = 0``. Only the
  hemisphere carries pixels; it composites onto any background.
* **Exactly the unit disk** — image bounds map to ``x, y in [-1, 1]``
  (``margin=1.0``), disk inscribed and touching all four edges, row 0 at
  the top (``y = +1``). Square.

Sun and the synthetic ``Bw`` day/night pattern are skipped (not a
planet/satellite). Manual-only textures (e.g. Titan's default) are
skipped with a note rather than aborting. Big source maps are
downsampled before rendering so ``render_disk`` never balloons to
multi-GB float64 (Triton's map is 14138x7069).

Outputs
-------
* ``examples/figures/transparent/<body>_<view>.png``   per body & view
* ``examples/figures/transparent/_overview_<view>.png`` all disks of one
  view on a checkerboard (transparent corners show the squares through)
* ``examples/figures/transparent/README.txt``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from implanet import render_disk
from implanet.assets import get_texture
from implanet.assets._registry import texture_entries

OUT_DIR = Path(__file__).resolve().parent / "figures" / "transparent"

# Not planets/satellites: a star and a synthetic test pattern.
EXCLUDE = {"Sun", "Bw"}

SIZE = 512          # per-disk; extent is exactly [-1, 1] at any size
MAX_TEX = 4096      # downsample source maps wider than this (memory)

# name -> (view_direction = camera->center, up hint).
# Pole views: up cannot be parallel to the pole axis, so use +Y.
VIEWS = {
    "equator": ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),   # lat 0, lon 0
    "north":   ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),   # down the +Z pole
    "south":   ((0.0, 0.0, 1.0),  (0.0, 1.0, 0.0)),   # down the -Z pole
}


def _bodies() -> list[str]:
    seen: list[str] = []
    for e in texture_entries():
        b = e["body"]
        if b in EXCLUDE or b in seen:
            continue
        seen.append(b)
    return seen


def _rgba_texture(path: Path, max_tex: int) -> Image.Image:
    """Open, downsample if huge, and add an all-opaque alpha channel.

    render_disk leaves off-disk RGBA at alpha=0, so the disk mask itself
    (pixel-exact) is the only thing carrying transparency.
    """
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_tex:
        im.thumbnail((max_tex, max_tex))           # keeps 2:1, bounds RAM
    a = np.asarray(im)
    h, w, _ = a.shape
    return Image.fromarray(np.dstack([a, np.full((h, w), 255, np.uint8)]),
                           "RGBA")


def _checker(n: int = 16, tile: int = 1) -> np.ndarray:
    i, j = np.indices((n, n))
    c = ((i // tile + j // tile) % 2).astype(np.uint8)
    return np.where(c[..., None] == 1, 210, 235).astype(np.uint8) \
        * np.ones((1, 1, 3), np.uint8)


def _overview(vname: str, disks: list[tuple[str, np.ndarray]]) -> None:
    checker = _checker()
    ncol = 6
    nrow = -(-len(disks) // ncol)                    # ceil
    fig, axes = plt.subplots(nrow, ncol,
                             figsize=(2.2 * ncol, 2.2 * nrow))
    for ax in np.atleast_1d(axes).ravel():
        ax.axis("off")
    for ax, (body, img) in zip(np.atleast_1d(axes).ravel(), disks):
        ax.imshow(checker, extent=(-1, 1, -1, 1),
                  interpolation="nearest", zorder=0)
        # nearest: bilinear would blend the limb with the (0,0,0,0)
        # off-disk pixels and ring the disk dark.
        ax.imshow(img, extent=(-1, 1, -1, 1),
                  interpolation="nearest", zorder=1)
        ax.set_title(body, fontsize=10)
        ax.set_xlim(-1, 1); ax.set_ylim(-1, 1)
        ax.set_aspect("equal")
    fig.suptitle(f"implanet — transparent disks · {vname} view "
                 "(checkerboard shows through off-disk alpha=0)",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    ov = OUT_DIR / f"_overview_{vname}.png"
    fig.savefig(ov, dpi=120, facecolor="white")
    plt.close(fig)
    print(f"wrote {ov}  ({len(disks)} disks)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shade", action="store_true",
                    help="Lambertian sun at the sub-observer point "
                         "(default: flat).")
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--max-tex", type=int, default=MAX_TEX,
                    help="Downsample source maps wider than this.")
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sun = (1.0, 0.0, 0.0) if args.shade else None

    # results[view] = list of (body, rgba image)
    results: dict[str, list[tuple[str, np.ndarray]]] = {v: [] for v in VIEWS}
    bodies_done: list[str] = []
    skipped: list[str] = []

    for body in _bodies():
        try:
            tex = _rgba_texture(get_texture(body), args.max_tex)
        except Exception as exc:                     # manual-only / offline
            print(f"skip {body}: {exc}", file=sys.stderr)
            skipped.append(body)
            continue

        for vname, (vdir, vup) in VIEWS.items():
            img = render_disk(
                tex, view_direction=vdir, up=vup, sun_direction=sun,
                ambient=0.05, size=args.size, margin=1.0,
            )
            # margin=1.0 + RGBA texture → image exactly spans [-1, +1] and
            # carries an alpha channel that's 0 off-disk (full transparency).
            assert img.shape[-1] == 4

            dest = OUT_DIR / f"{body.lower()}_{vname}.png"
            Image.fromarray(img, "RGBA").save(dest)
            results[vname].append((body, img))
        bodies_done.append(body)
        print(f"wrote {body.lower()}_{{{','.join(VIEWS)}}}.png  "
              f"({args.size}x{args.size}, RGBA)")

    for vname, disks in results.items():
        if not disks:
            continue
        _overview(vname, disks)

    readme = OUT_DIR / "README.txt"
    readme.write_text(
        "implanet transparent disk exports\n"
        "=================================\n\n"
        "Square RGBA PNGs, named <body>_<view>.png, for views:\n"
        "    equator  sub-observer (lat 0, lon 0)\n"
        "    north    straight down the north pole (lat +90)\n"
        "    south    straight down the south pole (lat -90)\n\n"
        "Off-disk pixels have alpha=0. Image bounds map EXACTLY to:\n\n"
        "    x in [-1, 1]   (left edge -1, right edge +1)\n"
        "    y in [-1, 1]   (TOP row +1, bottom row -1)\n\n"
        "Disk inscribed, touching all four edges. Plot with extent\n"
        "[-1,1]x[-1,1]; row 0 is y=+1 (flip y if your imshow puts row 0\n"
        "at the bottom). Display with interpolation='nearest' (or fill\n"
        "off-disk RGB with the limb colour) to avoid a dark edge halo\n"
        "from blending into the transparent (0,0,0,0) pixels.\n\n"
        "Bodies: " + ", ".join(bodies_done) + "\n"
        + (("Skipped: " + ", ".join(skipped) + "\n") if skipped else "")
        + "See _overview_<view>.png for all disks on a checkerboard.\n"
    )
    print(f"wrote {readme}  ({len(bodies_done)} bodies x {len(VIEWS)} "
          f"views, {len(skipped)} skipped)")
    return 0 if bodies_done else 1


if __name__ == "__main__":
    raise SystemExit(main())
