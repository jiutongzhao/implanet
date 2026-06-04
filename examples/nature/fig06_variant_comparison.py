"""Figure 6 — Variant comparison: one body, several catalogued maps.

Core conclusion
---------------
Many bodies ship more than one map — different missions, instruments, or
colour processing. Rendered under identical view and Sun, the catalogue
lets you choose the map that fits the question (raw radiometry vs.
enhanced colour vs. a different mission's mosaic).

Layout
------
One row per body, one shaded orthographic disk per ``get_texture(body,
variant)``; each cell titled with its variant key. View (−X) and Sun
(1, 0.5, 0.3) are identical across every panel so only the map differs.
"""

from __future__ import annotations

import sys

from implanet import get_texture, render_disk
import _style as S

VIEW = (-1.0, 0.0, 0.0)
SUN = (1.0, 0.5, 0.3)

# Curated to a fixed 3-column grid; differences are visually instructive.
ROWS = [
    ("Mercury", ["sss", "messenger_bdr_mono", "messenger_enhanced_color"]),
    ("Earth",   ["blue_marble", "natural_earth3", "sss_daymap"]),
    ("Moon",    ["clementine_uvvis", "lroc_color_2019", "sss"]),
    ("Mars",    ["sss", "viking_mdim21_1km"]),
]


def main(size: int = 520) -> None:
    S.apply_style(font_size=8)
    import matplotlib.pyplot as plt

    ncol = max(len(v) for _, v in ROWS)
    nrow = len(ROWS)
    margin = 1.08

    fig, axes = plt.subplots(nrow, ncol, figsize=(ncol * 2.1, nrow * 2.35),
                             squeeze=False)
    for r, (body, variants) in enumerate(ROWS):
        for c in range(ncol):
            ax = axes[r][c]
            if c >= len(variants):
                ax.set_visible(False)
                continue
            variant = variants[c]
            try:
                img = render_disk(get_texture(body, variant),
                                  view_direction=VIEW, sun_direction=SUN,
                                  ambient=0.06, size=size, margin=margin,
                                  background=S.PLATE_BG)
                S.show_disk(ax, img, margin=margin)
            except Exception as exc:  # noqa: BLE001
                print(f"skip {body}/{variant}: {exc}", file=sys.stderr)
                ax.text(0.5, 0.5, "(unavailable)", ha="center", va="center",
                        transform=ax.transAxes, color=S.MUTED, fontsize=8)
            S.disk_ax(ax, title=variant)
            ax.title.set_family("monospace")
            ax.title.set_fontsize(7.5)
            if c == 0:
                ax.text(-0.14, 0.5, body, rotation=90, transform=ax.transAxes,
                        ha="center", va="center", color=S.INK, fontsize=11,
                        fontweight="bold")

    fig.suptitle("implanet — catalogued variants per body  ·  identical view "
                 "(−1, 0, 0) and Sun (1, 0.5, 0.3)",
                 fontsize=11, fontweight="bold", color=S.INK, y=0.997)
    fig.subplots_adjust(left=0.055, right=0.99, top=0.93, bottom=0.04,
                        wspace=0.06, hspace=0.22)
    S.caption(
        fig,
        "get_texture(body, variant) for each panel. Only the source map "
        "changes between cells in a row. Map credits in maps/manifest.json.",
        y=0.004)
    saved = S.finalize(fig, "fig06_variant_comparison")
    print("wrote", *[p.name for p in saved])


if __name__ == "__main__":
    main()
