"""Publication-style figures: one panel per manifest entry that has a
locally-downloaded texture, with sun direction from SPICE ephemerides
at a chosen UTC epoch.

Run after `python scripts/fetch_maps.py`. Output goes to
examples/figures_scientific/. Each filename is <body>_<variant>.png.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
# Some Wikimedia uploads (e.g. Mars Viking 21K×11K) trip PIL's
# decompression-bomb safeguard. These are legitimate maps, not attacks.
Image.MAX_IMAGE_PIXELS = None

from implanet.figure import plot_planet
from implanet.ephemeris import (
    sun_direction, sub_solar_point, ensure_kernels, known_bodies,
)


REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "maps" / "data"
OUT = REPO / "examples" / "figures_scientific"
MANIFEST = REPO / "maps" / "manifest.json"

EPOCH_UTC = os.environ.get("EPOCH", "2026-05-14T12:00:00")
VIEW_OFFSET_DEG = 30.0  # camera longitude offset from sub-solar

# Bodies that get no Lambertian shading (renders as full albedo).
NO_SHADING = {"Sun"}

# Per-variant ambient overrides (defaults to 0.05). Variants not listed
# get the default. Higher ambient = brighter terminator/night side.
AMBIENT = {
    "Earth.blue_marble":    0.10,
    "Earth.blue_marble_8k": 0.10,
    "Earth.sss_daymap":     0.10,
    "Earth.sss_clouds":     0.10,
    "Earth.sss_nightmap":   1.00,   # already a night map, render flat
    "Venus.sss_surface":    1.00,   # SAR mosaic, not an albedo image
    "Venus.sss_atmosphere": 0.30,
    "Jupiter.sss":              0.20,
    "Jupiter.cassini_pia07782": 0.18,
    "Saturn.sss":               0.20,
    "Uranus.sss":               0.25,
    "Neptune.sss":              0.22,
    "Sun.sss":                  1.00,
}


def latlon_view(lat_deg: float, lon_deg: float):
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    return (
        -math.cos(lat) * math.cos(lon),
        -math.cos(lat) * math.sin(lon),
        -math.sin(lat),
    )


def render_one(entry, out_path: Path):
    body = entry["body"]
    variant = entry.get("variant", "primary")
    fname = entry.get("filename")
    if not fname:
        return False
    path = DATA / fname
    if not path.exists():
        return False

    ambient = AMBIENT.get(f"{body}.{variant}", 0.05)

    # Use SPICE only if (a) body is in ephemerides and (b) we want shading.
    sun_vec = None
    sub_solar_str = ""
    view_vec = latlon_view(0, 30)  # neutral default
    if body in known_bodies() and body not in NO_SHADING:
        sun_vec = sun_direction(body, EPOCH_UTC)
        sslat, sslon = sub_solar_point(body, EPOCH_UTC)
        sub_solar_str = f"  sub-solar ({sslat:+.1f}°, {sslon:+.1f}°)"
        view_vec = latlon_view(sslat, sslon - VIEW_OFFSET_DEG)

    # For bodies we don't shade, choose a neutral equator view.
    title = f"{body}   variant: {variant}    {EPOCH_UTC} UTC"
    source = entry.get("citation", entry.get("description", ""))[:120]

    tex = Image.open(path).convert("RGB")
    fig, _ = plot_planet(
        tex,
        view_direction=view_vec,
        sun_direction=sun_vec,
        ambient=ambient,
        title=title,
        source_text=source,
        size=720,
        figsize=(7.0, 7.0),
    )
    fig.savefig(out_path, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {body}.{variant}{sub_solar_str}")
    return True


def main():
    ensure_kernels()
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads(MANIFEST.read_text())

    rendered = []
    skipped = []
    print(f"epoch: {EPOCH_UTC}")
    for entry in data["maps"]:
        body = entry["body"]
        variant = entry.get("variant", "primary")
        out_path = OUT / f"{body.lower()}_{variant}.png"
        if render_one(entry, out_path):
            rendered.append(out_path.name)
        else:
            skipped.append(f"{body}/{variant}")

    print(f"\nWrote {len(rendered)} figures to {OUT}")
    if skipped:
        print(f"  skipped (no local file): {len(skipped)}")


if __name__ == "__main__":
    main()
