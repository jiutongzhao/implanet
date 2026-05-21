"""Render every catalogued body's default texture into one gallery grid.

A snapshot of "what does implanet ship with" — one shaded orthographic
disk per body with an auto-fetchable default. Run from a checkout:

    python examples/texture_gallery.py

Writes ``examples/figures_gallery/texture_gallery.png``. Manual-only
defaults (currently just Titan) are skipped automatically.

Renders at full resolution (size=768, dpi=300). The committed preview
under ``docs/figures/gallery/`` is downsampled to keep the repo light;
re-run this script for the print-quality version.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from implanet import render_disk, get_texture
from implanet.assets._registry import texture_entries


OUT = Path(__file__).resolve().parent / "figures_gallery"
OUT.mkdir(parents=True, exist_ok=True)


def _default_entry_for_each_body():
    seen = {}
    for e in texture_entries():
        body = e["body"]
        if body in seen:
            continue
        if e.get("asset_url") or e.get("generator"):     # skip manual-only defaults
            seen[body] = e
    return seen


def main(size: int = 768) -> Path:
    bodies = _default_entry_for_each_body()
    n = len(bodies)
    cols = 4
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.6, rows * 2.7))
    axes = axes.ravel()

    # Fixed lighting & view so every disk reads consistently.
    view = (-1.0, 0.0, 0.0)
    sun  = (1.0, 0.5, 0.3)

    for ax, (body, entry) in zip(axes, bodies.items()):
        # Bodies that don't want shading: the Sun (it IS the light source)
        # and Venus/sss_surface (SAR pixels already encode reflectance —
        # we use sss_atmosphere as default, so this rarely fires).
        ambient = 1.0 if body == "Sun" else 0.05
        sd = None if body in {"Sun", "bw"} else sun

        img = render_disk(get_texture(body), view_direction=view,
                          sun_direction=sd, ambient=ambient,
                          size=size, margin=1.05, background="white")
        # Grayscale textures come back as 2D ndarrays — tell matplotlib
        # to render them as actual greyscale, not the default colormap.
        cmap = "gray" if img.ndim == 2 else None
        ax.imshow(img, extent=(-1.05, 1.05, -1.05, 1.05),
                  cmap=cmap, vmin=0, vmax=255)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        # How to fetch this disk: the default call resolves to the
        # variant shown in the second line.
        ax.set_title(f'get_texture("{body}")\n→ "{entry.get("variant","")}"',
                     fontsize=7, family="monospace")

    for ax in axes[n:]:
        ax.set_visible(False)

    fig.suptitle(f"implanet texture gallery — {n} bodies, default variant",
                 fontsize=12)
    # Extra row spacing so titles never collide with the disk above.
    fig.tight_layout(h_pad=3.0, rect=(0, 0, 1, 0.97))
    dest = OUT / "texture_gallery.png"
    fig.savefig(dest, dpi=300, bbox_inches="tight")
    print(f"wrote {dest}  ({n} panels)")
    return dest


if __name__ == "__main__":
    main()
