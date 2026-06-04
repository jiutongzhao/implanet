"""Figure 3 — Illumination: Lambertian shading and the sun_direction control.

Core conclusion
---------------
``sun_direction`` (planet → Sun) drives a Lambertian term
``ambient + (1-ambient)·max(0, n·ŝ)``: holding the camera fixed and
sweeping the Sun reproduces the phase cycle (top row); holding the Sun
fixed and moving the camera samples named illumination geometries
(bottom row). In both, the day/night terminator (gold) is the great
circle ``n·ŝ = 0``.

Panels
------
top    phase sweep — fixed camera (sub-observer lon 0), sub-solar
       longitude −135°…+135°: crescent → full → crescent.
bottom five named field-of-view geometries with the Sun fixed at +X:
       sun · terminator · antisun · north pole · south pole.

Moon (NASA SVS / LROC colour mosaic).
"""

from __future__ import annotations

import math

from implanet import get_texture, render_disk
import _style as S


def latlon_view(lat_deg: float, lon_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (-math.cos(lat) * math.cos(lon),
            -math.cos(lat) * math.sin(lon),
            -math.sin(lat))


def latlon_sun(lat_deg: float, lon_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat))


# Bottom row: Sun fixed at +X; each view is (name, view_direction, up, ambient)
SUN_FIXED = (1.0, 0.0, 0.0)
FOVS = [
    ("sun",        (-1.0, 0.0, 0.0), (0, 0, 1), 0.10),
    ("terminator", (0.0, -1.0, 0.0), (0, 0, 1), 0.08),
    ("antisun",    (1.0, 0.0, 0.0),  (0, 0, 1), 0.22),
    ("north pole", (0.0, 0.0, -1.0), (1, 0, 0), 0.08),
    ("south pole", (0.0, 0.0, 1.0),  (1, 0, 0), 0.08),
]

PHASES = [-135, -67, 0, 67, 135]   # sub-solar longitude (deg)


def main() -> None:
    S.apply_style(font_size=8)
    moon = get_texture("Moon", "lroc_color_2019")

    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(8.4, 3.9))
    gs = fig.add_gridspec(2, 5, hspace=0.42, wspace=0.08)
    margin = 1.1

    # ── top row: phase sweep (camera fixed at lon 0) ─────────────────────
    view = latlon_view(0, 0)
    for col, sun_lon in enumerate(PHASES):
        ax = fig.add_subplot(gs[0, col])
        sun = latlon_sun(0, sun_lon)
        img = render_disk(moon, view_direction=view, sun_direction=sun,
                          ambient=0.04, size=480, margin=margin,
                          background=S.PLATE_BG)
        S.show_disk(ax, img, margin=margin)
        S.disk_ax(ax, title=f"sub-solar {sun_lon:+d}°")
        S.draw_limb(ax)
        S.draw_terminator(ax, view, sun)
        if col == 0:
            S.panel_label(ax, "a")
            ax.text(-0.18, 0.5, "phase sweep\n(camera fixed)", rotation=90,
                    transform=ax.transAxes, ha="center", va="center",
                    color=S.INK, fontsize=7.5, fontweight="bold")

    # ── bottom row: named illumination FOVs (Sun fixed at +X) ────────────
    for col, (name, vdir, up, amb) in enumerate(FOVS):
        ax = fig.add_subplot(gs[1, col])
        img = render_disk(moon, view_direction=vdir, up=up,
                          sun_direction=SUN_FIXED, ambient=amb, size=480,
                          margin=margin, background=S.PLATE_BG)
        S.show_disk(ax, img, margin=margin)
        S.disk_ax(ax, title=name)
        S.draw_limb(ax)
        S.draw_terminator(ax, vdir, SUN_FIXED, up=up)
        if col == 0:
            S.panel_label(ax, "b")
            ax.text(-0.18, 0.5, "named FOVs\n(Sun fixed +X)", rotation=90,
                    transform=ax.transAxes, ha="center", va="center",
                    color=S.INK, fontsize=7.5, fontweight="bold")

    fig.suptitle("implanet — sun_direction drives Lambertian shading",
                 fontsize=11, fontweight="bold", color=S.INK, y=1.0)
    fig.subplots_adjust(left=0.055, right=0.99, top=0.86, bottom=0.10)
    S.caption(
        fig,
        "Moon, NASA SVS / LROC colour mosaic. Gold = day/night terminator "
        "(n·ŝ = 0). Top: ambient 0.04. Bottom: ambient 0.08–0.22 "
        "(antisun lifted so the night hemisphere stays readable).",
    )
    saved = S.finalize(fig, "fig03_illumination")
    print("wrote", *[p.name for p in saved])


if __name__ == "__main__":
    main()
