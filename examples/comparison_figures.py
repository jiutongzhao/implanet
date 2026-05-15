"""Side-by-side comparison panels for bodies with multiple texture variants.

Produces a single PNG per multi-variant body where each panel shows the
same view geometry (sub-camera point and SPICE sun direction) so that
the only difference between panels is the underlying processing.
"""

from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

from implanet.figure import plot_planet
from implanet.ephemeris import (
    sun_direction, sub_solar_point, ensure_kernels, known_bodies,
)


REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "maps" / "data"
OUT = REPO / "examples" / "figures_comparison"
MANIFEST = REPO / "maps" / "manifest.json"
EPOCH_UTC = os.environ.get("EPOCH", "2026-05-14T12:00:00")
VIEW_OFFSET_DEG = 30.0

# Bodies rendered without Lambertian shading.
NO_SHADING = {"Sun"}

# Per-variant ambient overrides; same defaults as scientific_figures.py.
AMBIENT = {
    "Earth.sss_nightmap":   1.00,
    "Venus.sss_surface":    1.00,
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


def render_panel(ax, entry, view_vec, sun_vec, ambient):
    fname = entry["filename"]
    tex = Image.open(DATA / fname).convert("RGB")
    plot_planet(
        tex,
        view_direction=view_vec,
        sun_direction=sun_vec,
        ambient=ambient,
        title=f"{entry['body']}  ·  {entry.get('variant')}",
        source_text=entry.get("citation", "")[:90],
        size=520,
        ax=ax,
    )


def make_comparison(body: str, entries: list, out_path: Path):
    # Filter to entries that have a downloaded file.
    entries = [e for e in entries if e.get("filename")
               and (DATA / e["filename"]).exists()]
    if len(entries) < 2:
        return False

    # Sort variants alphabetically for stable layout.
    entries.sort(key=lambda e: e.get("variant", ""))

    use_spice = body in known_bodies() and body not in NO_SHADING
    sun_vec = None
    view_vec = latlon_view(0, 30)
    epoch_str = ""
    if use_spice:
        sun_vec = sun_direction(body, EPOCH_UTC)
        sslat, sslon = sub_solar_point(body, EPOCH_UTC)
        view_vec = latlon_view(sslat, sslon - VIEW_OFFSET_DEG)
        epoch_str = f" — sub-solar ({sslat:+.1f}°, {sslon:+.1f}°) at {EPOCH_UTC} UTC"

    n = len(entries)
    cols = min(n, 2 if n <= 4 else 3)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(6.0 * cols, 6.0 * rows),
                              squeeze=False)
    axes_flat = axes.flatten()

    for i, e in enumerate(entries):
        ambient = AMBIENT.get(f"{body}.{e.get('variant')}", 0.05)
        render_panel(axes_flat[i], e, view_vec, sun_vec, ambient)
    # Hide any leftover axes.
    for j in range(len(entries), len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(f"{body}: comparison of texture variants{epoch_str}",
                 fontsize=13, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return True


def main():
    ensure_kernels()
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads(MANIFEST.read_text())

    by_body = defaultdict(list)
    for e in data["maps"]:
        if e.get("asset_url"):
            by_body[e["body"]].append(e)

    print(f"epoch: {EPOCH_UTC}")
    written = []
    for body in sorted(by_body):
        if len(by_body[body]) < 2:
            continue
        out_path = OUT / f"{body.lower()}_variants.png"
        if make_comparison(body, by_body[body], out_path):
            print(f"  {body}: {len(by_body[body])} variants  -> {out_path.name}")
            written.append(out_path.name)

    print(f"\nWrote {len(written)} comparison figure(s) to {OUT}")


if __name__ == "__main__":
    main()
