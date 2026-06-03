"""Figure 5 — Catalogue gallery: every body's default texture.

Core conclusion
---------------
A single ``get_texture(body)`` call resolves each catalogued body to its
default map; rendered under one fixed view and Sun, the gallery is a
one-glance inventory of what ``implanet`` ships.

Layout
------
A quantitative grid of shaded orthographic disks, one per body with an
auto-fetchable default (manual-only defaults such as Titan are skipped).
Every disk uses the same camera (−X) and Sun (1, 0.5, 0.3); greyscale
maps render as true greyscale. The synthetic ``Bw`` pattern is omitted —
it is the subject of Figure 1.
"""

from __future__ import annotations

import math
import sys

from implanet import get_texture, render_disk
from implanet.assets._registry import texture_entries
import _style as S

EXCLUDE = {"Bw"}
VIEW = (-1.0, 0.0, 0.0)
SUN = (1.0, 0.5, 0.3)


def default_entries():
    seen = {}
    for e in texture_entries():
        b = e["body"]
        if b in EXCLUDE or b in seen:
            continue
        if e.get("asset_url") or e.get("generator"):   # auto-fetchable only
            seen[b] = e
    return seen


def main(size: int = 460) -> None:
    S.apply_style(font_size=8)
    import matplotlib.pyplot as plt

    bodies = default_entries()
    n = len(bodies)
    cols = 5
    rows = math.ceil(n / cols)
    margin = 1.08

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 1.7, rows * 1.92))
    axes = axes.ravel()

    for ax, (body, entry) in zip(axes, bodies.items()):
        # The Sun is its own light source (flat); SAR/synthetic stay flat too.
        flat = body in {"Sun"}
        sd = None if flat else SUN
        amb = 1.0 if flat else 0.06
        try:
            img = render_disk(get_texture(body), view_direction=VIEW,
                              sun_direction=sd, ambient=amb, size=size,
                              margin=margin, background=S.PLATE_BG)
        except Exception as exc:  # noqa: BLE001
            print(f"skip {body}: {exc}", file=sys.stderr)
            ax.set_visible(False)
            continue
        S.show_disk(ax, img, margin=margin)
        S.disk_ax(ax)
        ax.set_title(body, color=S.INK, fontsize=8.5, fontweight="bold",
                     pad=2)
        ax.text(0.5, -0.02, entry.get("variant", ""), transform=ax.transAxes,
                ha="center", va="top", color=S.MUTED, fontsize=6,
                family="monospace")

    for ax in axes[n:]:
        ax.set_visible(False)

    fig.suptitle(f"implanet — catalogue gallery · {n} bodies, default variant",
                 fontsize=12, fontweight="bold", color=S.INK, y=0.995)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.03,
                        wspace=0.06, hspace=0.30)
    S.caption(
        fig,
        "Each disk: get_texture(body) under a fixed view (−1, 0, 0) and Sun "
        "(1, 0.5, 0.3), ambient 0.06 (Sun rendered flat). Map credits in "
        "maps/manifest.json.", y=0.004)
    saved = S.finalize(fig, "fig05_texture_gallery")
    print("wrote", *[p.name for p in saved], f"({n} bodies)")


if __name__ == "__main__":
    main()
