"""Demo of the synthetic day/night reference texture.

Shows the equirectangular source plus three orthographic views that make
the texture's purpose obvious: it encodes which hemisphere is which, so
you can confirm a `view_direction` shows the longitude you expect.

Render it FLAT (no sun_direction) — the day/night split is baked in.

Output: examples/figures/reference_daynight.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from implanet import render_disk
from implanet.assets import get_texture

OUT = Path(__file__).resolve().parent / "figures" / "reference_daynight.png"


def _view_from_lon(lon_deg: float):
    """Camera -> center for an equatorial sub-observer at `lon_deg`."""
    lon = np.radians(lon_deg)
    return (-np.cos(lon), -np.sin(lon), 0.0)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tex = Image.open(get_texture("bw", "daynight")).convert("RGB")

    fig = plt.figure(figsize=(11, 6.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.15])

    # Top row spans all three columns: the raw equirectangular texture.
    ax0 = fig.add_subplot(gs[0, :])
    ax0.imshow(np.asarray(tex), extent=(-180, 180, -90, 90), aspect="auto")
    ax0.set_xticks(np.arange(-180, 181, 30))
    ax0.set_yticks(np.arange(-90, 91, 30))
    ax0.set_xlabel("longitude (°)")
    ax0.set_ylabel("latitude (°)")
    ax0.set_title("source texture — white day (lon 0), grey shaded side "
                  "(lon ±180); 30° graticule")

    # Bottom row: three orthographic views.
    margin = 1.05
    for col, lon in enumerate((0, 90, 180)):
        ax = fig.add_subplot(gs[1, col])
        img = render_disk(tex, view_direction=_view_from_lon(lon),
                          size=420, margin=margin,    # flat: no sun
                          background=(255, 255, 255))  # white off-disk
        ax.imshow(img, extent=(-margin, margin, -margin, margin),
                  origin="upper")
        ax.set_aspect("equal")
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
        ax.set_title(f"sub-observer lon {lon:+d}°")

    fig.suptitle("implanet — day/night reference texture", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT, dpi=130, facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
