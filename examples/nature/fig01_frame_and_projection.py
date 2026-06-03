"""Figure 1 — Body-fixed frame and the projection convention.

Core conclusion
---------------
`implanet` reads an equirectangular map (row 0 = north pole, column 0 at
longitude ``lon0``) and projects it orthographically into the body-fixed
IAU frame; ``view_direction`` (camera → centre) selects which hemisphere
faces the viewer, and the sub-observer point lands at the disk centre.

Panels
------
a  the shipped synthetic day/night reference map (equirectangular source),
   30° graticule, with the white dayside at longitude 0 (+X).
b–d three orthographic views of that same map at sub-observer longitude
   0°, 90°, 180° — graticule + limb overlays prove the geometry, and the
   sub-observer cross sits exactly at disk centre.

Uses only the bundled ``Bw/daynight`` texture, so it needs no downloads.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from implanet import get_texture, render_disk
import _style as S


def view_from_lon(lon_deg: float):
    """Camera → centre for an equatorial sub-observer at `lon_deg`."""
    lon = np.radians(lon_deg)
    return (-np.cos(lon), -np.sin(lon), 0.0)


def main() -> None:
    S.apply_style(font_size=8)
    tex = Image.open(get_texture("Bw", "daynight")).convert("RGB")

    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(7.2, 5.0))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.18], hspace=0.32,
                          wspace=0.12)

    # ── a: equirectangular source ────────────────────────────────────────
    ax0 = fig.add_subplot(gs[0, :])
    ax0.imshow(np.asarray(tex), extent=(-180, 180, -90, 90), aspect="auto",
               interpolation="nearest")
    ax0.set_xticks(np.arange(-180, 181, 60))
    ax0.set_yticks(np.arange(-90, 91, 45))
    ax0.set_xlabel("longitude  (°)")
    ax0.set_ylabel("latitude  (°)")
    ax0.set_title("equirectangular source — dayside at lon 0 (+X), "
                  "row 0 = north pole", color=S.INK, pad=4)
    ax0.tick_params(length=2.5)
    S.panel_label(ax0, "a", color=S.INK, x=-0.075, y=1.16)

    # ── b–d: three sub-observer longitudes ───────────────────────────────
    margin = 1.12
    for col, (lon, lab) in enumerate(zip((0, 90, 180), "bcd")):
        ax = fig.add_subplot(gs[1, col])
        view = view_from_lon(lon)
        img = render_disk(tex, view_direction=view, size=560, margin=margin,
                          background=S.PLATE_BG)   # flat: day/night is baked in
        S.show_disk(ax, img, margin=margin)
        S.disk_ax(ax, title=f"sub-observer lon {lon:+d}°")
        S.draw_graticule(ax, view)
        S.draw_limb(ax)
        S.mark_subobserver(ax, view)
        S.panel_label(ax, lab)

    fig.suptitle("implanet — body-fixed frame & the view_direction convention",
                 fontsize=11, fontweight="bold", color=S.INK, y=0.99)
    S.caption(
        fig,
        "Synthetic Bw/daynight reference map (bundled; no download). "
        "view_direction points camera → planet centre; the sub-observer "
        "point (cyan +) is always the disk centre. Graticule at 30°.",
    )
    saved = S.finalize(fig, "fig01_frame_and_projection")
    print("wrote", *[p.name for p in saved])


if __name__ == "__main__":
    main()
