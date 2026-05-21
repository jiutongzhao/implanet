"""Export every body as transparent disks from five illumination FOVs.

For a fixed sun at +X (sub-solar at lon 0, equator), each body is rendered
from five camera vantages, Lambertian-shaded, on a transparent background:

* ``sun``         — camera on the Sun→body line: the fully-lit dayside.
* ``antisun``     — opposite side: the night hemisphere (ambient only).
* ``terminator``  — 90° from the Sun: day/night split down the middle.
* ``north_pole``  — straight down the +Z pole (sun grazes from one side).
* ``south_pole``  — straight down the −Z pole.

Every PNG is RGBA with off-disk ``alpha = 0`` on an exact ``[-1, 1]`` grid
(``margin=1.0``), so users can drop a disk onto any background. The
transparent fill is black, so downscaling never rings the limb with a
white halo.

Output: ``figures/disk_views/<body>_<view>.png`` (committed — grab
directly), plus ``figures/disk_views/README.md``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from implanet import render_disk
from implanet.assets import get_texture
from implanet.assets._registry import texture_entries

OUT_DIR = Path(__file__).resolve().parent.parent / "figures" / "disk_views"

EXCLUDE = {"Sun", "Bw"}          # a star and a synthetic test pattern
SUN = (1.0, 0.0, 0.0)            # sub-solar at lon 0, equator
AMBIENT = 0.20                   # shaded-side floor (terminator / pole views)
# Per-view ambient overrides:
#  * sun     — the disk is fully lit, but pure-Lambertian cos falloff
#              darkens the limb to near-black (a real full-phase body
#              looks flatter). Lift it so limb darkening is gentle.
#  * antisun — sees only the night hemisphere (cos i = 0 everywhere), so
#              the whole disk renders at the floor; lift it to stay readable.
# terminator / north_pole / south_pole keep the low default so their
# day-night contrast stays crisp.
AMBIENT_BY_VIEW = {"sun": 0.50, "antisun": 0.30}
SIZE = 1024
MAX_TEX = 4096                   # downsample huge source maps (memory)

# view name -> (view_direction = camera->centre, up hint)
VIEWS = {
    "sun":        ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),   # fully lit dayside
    "antisun":    (( 1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),   # night hemisphere
    "terminator": (( 0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),  # day/night split
    "north_pole": (( 0.0, 0.0, -1.0), (1.0, 0.0, 0.0)),  # down the +Z pole
    "south_pole": (( 0.0, 0.0,  1.0), (1.0, 0.0, 0.0)),  # down the -Z pole
}


def _bodies() -> list[str]:
    seen: list[str] = []
    for e in texture_entries():
        b = e["body"]
        if b not in EXCLUDE and b not in seen:
            seen.append(b)
    return seen


def _rgba_texture(path: Path, max_tex: int) -> Image.Image:
    """Open, downsample if huge, add an all-opaque alpha channel so the
    only transparency in the output is the off-disk mask."""
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_tex:
        im.thumbnail((max_tex, max_tex))            # keeps 2:1, bounds RAM
    a = np.asarray(im)
    h, w, _ = a.shape
    return Image.fromarray(np.dstack([a, np.full((h, w), 255, np.uint8)]),
                           "RGBA")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--max-tex", type=int, default=MAX_TEX)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done: list[str] = []
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
                tex, view_direction=vdir, up=vup, sun_direction=SUN,
                ambient=AMBIENT_BY_VIEW.get(vname, AMBIENT),
                size=args.size, margin=1.0,
                background=(0, 0, 0),                 # transparent pixels = black
            )
            assert img.shape[-1] == 4                 # RGBA, off-disk alpha=0
            dest = OUT_DIR / f"{body.lower()}_{vname}.png"
            Image.fromarray(img, "RGBA").save(dest, optimize=True)
        done.append(body)
        print(f"wrote {body.lower()}_{{{','.join(VIEWS)}}}.png "
              f"({args.size}x{args.size} RGBA)")

    _write_readme(done, skipped)
    print(f"\n{len(done)} bodies x {len(VIEWS)} views "
          f"-> {OUT_DIR}  ({len(skipped)} skipped)")
    return 0 if done else 1


def _write_readme(done: list[str], skipped: list[str]) -> None:
    views = list(VIEWS)
    # body x view gallery (HTML so thumbnails can be sized small)
    rows = ["<tr><th align=\"left\">body</th>"
            + "".join(f"<th>{v}</th>" for v in views) + "</tr>"]
    for body in done:
        cells = "".join(
            f'<td align="center">'
            f'<img src="{body.lower()}_{v}.png" width="110" '
            f'alt="{body} {v}"></td>'
            for v in views
        )
        rows.append(f'<tr><td align="left"><b>{body}</b></td>{cells}</tr>')
    table = "<table>\n" + "\n".join(rows) + "\n</table>"

    (OUT_DIR / "README.md").write_text(
        "# Transparent disk views\n\n"
        "Ready-to-use **RGBA** disks, one per body and illumination FOV, "
        "named `<body>_<view>.png`. Off-disk pixels are fully transparent "
        "(`alpha = 0`); the image spans exactly `x, y in [-1, 1]` "
        "(disk inscribed, row 0 = `y = +1`). Grab any file directly.\n\n"
        "Sun fixed at +X (sub-solar at lon 0, equator); Lambertian-shaded, "
        f"ambient {AMBIENT} for terminator/pole views, "
        f"{AMBIENT_BY_VIEW['sun']} for `sun` (gentle limb darkening on the "
        f"fully-lit disk) and {AMBIENT_BY_VIEW['antisun']} for `antisun` "
        "(readable night side).\n\n"
        "| view | camera | shows |\n"
        "|---|---|---|\n"
        "| `sun` | Sun→body line | fully-lit dayside |\n"
        "| `antisun` | opposite the Sun | night hemisphere |\n"
        "| `terminator` | 90° from the Sun | day/night split down the middle |\n"
        "| `north_pole` | down the +Z pole | pole-on, sun grazing one side |\n"
        "| `south_pole` | down the −Z pole | pole-on |\n\n"
        "Display with `interpolation='nearest'` (or composite over a "
        "background) to avoid blending the limb into the transparent "
        "pixels.\n\n"
        "## Gallery\n\n"
        + table + "\n\n"
        + (("Skipped (manual-only / unavailable): "
            + ", ".join(skipped) + "\n") if skipped else "")
    )


if __name__ == "__main__":
    raise SystemExit(main())
