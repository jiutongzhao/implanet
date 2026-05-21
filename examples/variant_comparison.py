"""Per-body grids comparing every auto-fetchable variant we ship.

Some bodies have several catalogued textures — different missions,
different processing (raw vs. enhanced colour, day vs. night, ESA vs
USGS, etc.). This script renders each variant side-by-side under
identical lighting so the differences are easy to see.

    python examples/variant_comparison.py

Writes one PNG per multi-variant body to ``examples/figures_gallery/``.

Renders at full resolution (size=1024, dpi=300). The committed previews
under ``figures/gallery/`` are downsampled to keep the repo light;
re-run this script for the print-quality versions.
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

# Some catalogued variants (USGS full-res, etc.) are larger than PIL's
# default decompression-bomb threshold; we trust the registry.
Image.MAX_IMAGE_PIXELS = None

from implanet import render_disk, get_texture
from implanet.assets._registry import texture_entries


OUT = Path(__file__).resolve().parent / "figures_gallery"
OUT.mkdir(parents=True, exist_ok=True)

# Hard cap: skip variants whose registered size exceeds this. The full-res
# USGS mosaics (Mars Viking MDIM 232m = ~12 GB) are catalogued but make
# no sense to download for a thumbnail gallery.
LARGE_THRESHOLD_BYTES = 200 * 1024 * 1024


def _auto_variants_by_body():
    grouped = defaultdict(list)
    for e in texture_entries():
        if not (e.get("asset_url") or e.get("generator")):
            continue
        sz = e.get("size_bytes_estimated")
        if sz and sz > LARGE_THRESHOLD_BYTES:
            print(f"  skip {e['body']}/{e['variant']}: "
                  f"{sz / 1024 / 1024:.0f} MB (> threshold)",
                  file=sys.stderr)
            continue
        grouped[e["body"]].append(e)
    return {b: vs for b, vs in grouped.items() if len(vs) > 1}


def render_body_variants(body: str, variants, size: int = 1024) -> Path:
    n = len(variants)
    # Squarer grids: a single row for ≤3 variants, else as close to
    # square as possible (6 → 3×2, 4 → 2×2).
    cols = n if n <= 3 else math.ceil(math.sqrt(n))
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 3.7),
                             squeeze=False)
    axes = axes.ravel()

    view = (-1.0, 0.0, 0.0)
    sun  = (1.0, 0.5, 0.3)

    for ax, entry in zip(axes, variants):
        ambient = 1.0 if body == "Sun" else 0.05
        sd = None if body in {"Sun", "Bw"} else sun
        try:
            img = render_disk(get_texture(body, entry["variant"]),
                              view_direction=view, sun_direction=sd,
                              ambient=ambient, size=size, margin=1.05,
                              background="white")
            cmap = "gray" if img.ndim == 2 else None
            ax.imshow(img, extent=(-1.05, 1.05, -1.05, 1.05),
                      cmap=cmap, vmin=0, vmax=255)
        except Exception as exc:                       # manual-only, oversize, etc.
            print(f"  skip {body}/{entry['variant']}: {exc}", file=sys.stderr)
            ax.text(0.5, 0.5, "(unavailable)", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10, color="0.6")
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        # Show exactly how to fetch this variant.
        ax.set_title(f'get_texture("{body}", "{entry["variant"]}")',
                     fontsize=8, family="monospace")

    for ax in axes[n:]:
        ax.set_visible(False)

    fig.suptitle(f"{body} — {n} catalogued variants  ·  "
                 f"identical view (-1,0,0) and sun (1, 0.5, 0.3)",
                 fontsize=12)
    # Extra row spacing so a panel's title never collides with the disk
    # in the row above; leave headroom for the suptitle.
    fig.tight_layout(h_pad=3.0, rect=(0, 0, 1, 0.96))
    dest = OUT / f"variants_{body.lower()}.png"
    fig.savefig(dest, dpi=300, bbox_inches="tight")
    print(f"wrote {dest}  ({body}, {n} variants)")
    return dest


def main() -> list:
    written = []
    for body, vs in _auto_variants_by_body().items():
        written.append(render_body_variants(body, vs))
    return written


if __name__ == "__main__":
    main()
