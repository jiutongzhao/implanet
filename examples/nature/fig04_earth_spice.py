"""Figure 4 — SPICE-driven geometry at a real instant.

Core conclusion
---------------
Fed real ``sun_direction``/sub-solar geometry from SPICE, ``implanet``
poses the body physically: the orthographic disk shows the true sunlit
face, and ``render_flatmap`` re-shades the whole map so the day/night
terminator is a single great circle — both for the same UTC.

Panels
------
a  orthographic Blue Marble with the camera on the Sun→Earth line
   (sub-observer = sub-solar): the fully lit hemisphere, northern tilt
   toward the viewer near the June solstice.
b  the same epoch as an equirectangular flat map, rotated so the
   sub-solar point sits at display longitude 0; gold = the global
   day/night terminator from ``flatmap_terminator``.

Caption text is taken verbatim from ``render_info``. Needs the SPICE
kernels (downloaded on first ephemeris call).
"""

from __future__ import annotations

import sys

import numpy as np
from PIL import Image

from implanet import (get_texture, render_disk, render_flatmap, render_info,
                      sun_direction, sub_solar_point, ensure_kernels)
import _style as S

UTC = "2026-06-21T12:00:00"   # near the June solstice


def main() -> int:
    S.apply_style(font_size=8)
    try:
        ensure_kernels()
        sun = sun_direction("Earth", UTC)
        sslat, sslon = sub_solar_point("Earth", UTC)
    except Exception as exc:  # noqa: BLE001
        print(f"SPICE lookup failed: {exc}", file=sys.stderr)
        return 1

    earth_path = get_texture("Earth", "blue_marble")
    view = tuple(-float(c) for c in sun)        # sub-observer = sub-solar

    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(8.6, 4.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.62], wspace=0.16)

    # ── a: fully sunlit orthographic disk ────────────────────────────────
    margin = 1.1
    axa = fig.add_subplot(gs[0, 0])
    img = render_disk(earth_path, view_direction=view, sun_direction=sun,
                      ambient=0.04, size=720, margin=margin,
                      background=S.PLATE_BG)
    S.show_disk(axa, img, margin=margin)
    S.disk_ax(axa, title="orthographic disk — sunlit hemisphere")
    S.draw_graticule(axa, view)
    S.draw_limb(axa)
    S.mark_subsolar(axa, view, sun)
    S.mark_subobserver(axa, view, label=False)
    S.panel_label(axa, "a")

    # ── b: flat map for the same epoch, terminator overlaid ──────────────
    tex = Image.open(earth_path).convert("RGB")
    flat = render_flatmap(tex, rotation_lon_deg=sslon, sun_direction=sun,
                          ambient=0.10, output_size=(1024, 2048),
                          return_array=True)
    axb = fig.add_subplot(gs[0, 1])
    axb.imshow(flat, extent=(-180, 180, -90, 90), aspect="auto",
               origin="upper", interpolation="bilinear", zorder=0)
    S.draw_flatmap_terminator(axb, sun, rotation_lon_deg=sslon)
    axb.plot(0, sslat, marker="*", color=S.SUN, ms=11, mec="white", mew=0.6,
             zorder=6)                                   # sub-solar point
    axb.set_xticks(np.arange(-180, 181, 60))
    axb.set_yticks(np.arange(-90, 91, 45))
    axb.set_xlabel("display longitude  (°)  —  sub-solar centred at 0")
    axb.set_ylabel("latitude  (°)")
    axb.set_xlim(-180, 180)
    axb.set_ylim(-90, 90)
    axb.grid(True, color="white", alpha=0.18, lw=0.4)
    axb.tick_params(length=2.5)
    axb.set_title("equirectangular flat map — global terminator",
                  color=S.INK, pad=4)
    S.panel_label(axb, "b")

    info = render_info(earth_path, view_direction=view, sun_direction=sun,
                       ambient=0.04)
    fig.suptitle(f"implanet — SPICE geometry for Earth at {UTC} UTC",
                 fontsize=11, fontweight="bold", color=S.INK, y=1.0)
    fig.subplots_adjust(left=0.045, right=0.99, top=0.88, bottom=0.16)
    S.caption(fig, "render_info: " + info["caption"]
              + f"  ·  sub-solar ({sslat:+.1f}°, {sslon:+.1f}°E).")
    saved = S.finalize(fig, "fig04_earth_spice")
    print("wrote", *[p.name for p in saved])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
