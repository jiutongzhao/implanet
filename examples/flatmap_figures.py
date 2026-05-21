"""Flat-map (equirectangular) demo: one panel per body that has a local
texture and a SPICE-known ephemeris. Each output applies both
transforms `render_flatmap` exposes:

  * **rotation** — `rotation_lon_deg` is set to the sub-solar longitude
    at the chosen epoch, so the day side ends up centered at display
    longitude 0. This makes the rotation visibly meaningful: the bright
    peak moves to a different column than in the raw texture.

  * **shadow** — `sun_direction` is the real planet→Sun unit vector at
    the epoch (from SPICE), so each pixel is dimmed by the Lambertian
    cosine. The terminator is a great-circle arc visible as the
    transition from bright to ambient.

Output: examples/figures_flatmap/<body>_<variant>.png

Run after `python scripts/fetch_maps.py`. Override the epoch via:

    EPOCH="2025-12-21T18:00:00" python examples/flatmap_figures.py
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

from implanet import render_flatmap, get_texture
from implanet.assets import texture_entries
from implanet.ephemeris import (
    sun_direction, sub_solar_point, ensure_kernels, known_bodies,
)


REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "examples" / "figures_flatmap"

EPOCH_UTC = os.environ.get("EPOCH", "2026-05-14T12:00:00")

# Per-variant ambient overrides (default 0.05). Lower = darker night side.
AMBIENT = {
    "Earth.blue_marble":    0.10,
    "Earth.blue_marble_8k": 0.10,
    "Earth.sss_daymap":     0.10,
    "Earth.sss_clouds":     0.10,
    "Jupiter.sss":              0.20,
    "Jupiter.cassini_pia07782": 0.18,
    "Saturn.sss":               0.20,
    "Uranus.sss":               0.25,
    "Neptune.sss":              0.22,
}


def render_one(entry, out_path: Path) -> bool:
    body = entry["body"]
    variant = entry.get("variant", "primary")
    if body not in known_bodies():
        return False   # no SPICE → no real sun, skip
    # Use only textures already in the cache (dev checkout or pip cache);
    # don't force downloads from this "render whatever you have" demo.
    try:
        path = get_texture(body, entry.get("variant"),
                           download_if_missing=False)
    except (FileNotFoundError, ValueError, KeyError):
        return False

    ambient = AMBIENT.get(f"{body}.{variant}", 0.05)

    sun = sun_direction(body, EPOCH_UTC)
    sslat, sslon = sub_solar_point(body, EPOCH_UTC)

    tex = Image.open(path).convert("RGB")
    arr = render_flatmap(
        tex,
        rotation_lon_deg=sslon,   # center the sub-solar point at display lon 0
        sun_direction=sun,
        ambient=ambient,
        output_size=(1024, 2048),   # cap output so giant maps (21k Viking) stay sane
        return_array=True,
    )

    # Fixed figure + axes layout so every panel saves at identical pixel
    # dimensions and the data area lands at the same place. The axes box
    # is set to width:height = 2:1 in inches so a 2:1 flat map renders
    # without distortion under aspect="auto".
    fig = plt.figure(figsize=(10.0, 5.7), dpi=130)
    # axes_w = 0.88 * 10 = 8.8 in,  axes_h = 0.77 * 5.7 ≈ 4.39 in  → 2.00:1
    ax = fig.add_axes([0.07, 0.13, 0.88, 0.77])
    ax.imshow(arr, extent=(-180.0, 180.0, -90.0, 90.0),
              aspect="auto", interpolation="bilinear", origin="upper")
    ax.set_xticks(np.arange(-180, 181, 30))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.set_xlabel("display longitude  (°)")
    ax.set_ylabel("latitude  (°)")
    ax.grid(True, linestyle="--", linewidth=0.5,
            color="white", alpha=0.45)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_title(
        f"{body} — {variant}    {EPOCH_UTC} UTC\n"
        f"rotation = {sslon:+.1f}°    sub-solar = ({sslat:+.1f}°, {sslon:+.1f}°)",
        fontsize=10,
    )
    fig.savefig(out_path, dpi=130, facecolor="white")
    plt.close(fig)
    print(f"  {body}.{variant}  sub-solar ({sslat:+.1f}°, {sslon:+.1f}°)"
          f"  rotation={sslon:+.1f}°")
    return True


def main():
    ensure_kernels()
    OUT.mkdir(parents=True, exist_ok=True)

    rendered = []
    skipped = []
    print(f"epoch: {EPOCH_UTC}")
    for entry in texture_entries():
        body = entry["body"]
        variant = entry.get("variant", "primary")
        out_path = OUT / f"{body.lower()}_{variant}.png"
        if render_one(entry, out_path):
            rendered.append(out_path.name)
        else:
            skipped.append(f"{body}/{variant}")

    print(f"\nWrote {len(rendered)} flat maps to {OUT}")
    if skipped:
        print(f"  skipped (no local file or no SPICE coverage): {len(skipped)}")


if __name__ == "__main__":
    main()
