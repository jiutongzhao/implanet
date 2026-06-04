"""Figure 2 — Viewing geometry: one body, four camera vantages.

Core conclusion
---------------
A single ``view_direction`` (plus an ``up`` hint that fixes the camera
roll) selects any vantage on the body; the sub-observer point always
maps to disk centre and the graticule re-projects accordingly — equator,
oblique, and straight down a pole are all the same one call.

Panels
------
a equator, 0°E      b equator, 100°E
c north pole (up = +X fixes the roll)   d oblique, 45°N 60°W

The Sun is held fixed in the body-fixed frame across all four panels, so
the day/night terminator (gold) sweeps with the camera, not with the
lighting. Earth (NASA Blue Marble).
"""

from __future__ import annotations

import math

from implanet import get_texture, render_disk
import _style as S


def view_from_latlon(lat_deg: float, lon_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (-math.cos(lat) * math.cos(lon),
            -math.cos(lat) * math.sin(lon),
            -math.sin(lat))


def sun_from_latlon(lat_deg: float, lon_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat))


def main() -> None:
    S.apply_style(font_size=8)
    earth = get_texture("Earth", "blue_marble")

    import matplotlib.pyplot as plt

    sun = sun_from_latlon(20, -40)        # fixed in the body-fixed frame
    margin = 1.12
    cases = [
        ("a", "equator, 0°E",        view_from_latlon(0, 0),    (0, 0, 1)),
        ("b", "equator, 100°E",      view_from_latlon(0, 100),  (0, 0, 1)),
        ("c", "north pole (up = +X)", view_from_latlon(89, 0),  (1, 0, 0)),
        ("d", "oblique, 45°N 60°W",  view_from_latlon(45, -60), (0, 0, 1)),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(5.6, 6.0))
    for ax, (lab, title, view, up) in zip(axes.ravel(), cases):
        img = render_disk(earth, view_direction=view, up=up, sun_direction=sun,
                          ambient=0.06, size=620, margin=margin,
                          background=S.PLATE_BG)
        S.show_disk(ax, img, margin=margin)
        S.disk_ax(ax, title=title)
        S.draw_graticule(ax, view, up=up)
        S.draw_limb(ax)
        S.draw_terminator(ax, view, sun, up=up)
        S.mark_subobserver(ax, view, up=up)
        S.mark_subsolar(ax, view, sun, up=up)
        S.panel_label(ax, lab)

    fig.suptitle("implanet — one view_direction picks any vantage",
                 fontsize=11, fontweight="bold", color=S.INK, y=0.985)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.06,
                        wspace=0.06, hspace=0.16)
    S.caption(
        fig,
        "Earth, NASA Blue Marble. Sun fixed in the body-fixed frame "
        "(sub-solar 20°N 40°W); gold = day/night terminator and sub-solar "
        "point, cyan + = sub-observer. Graticule at 30°.",
    )
    saved = S.finalize(fig, "fig02_viewing_geometry")
    print("wrote", *[p.name for p in saved])


if __name__ == "__main__":
    main()
