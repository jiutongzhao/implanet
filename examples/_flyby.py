"""Shared helper for spacecraft-flyby reproductions.

Each per-mission script supplies its UTC, body, NAIF spacecraft name,
and which SPK files to furnish; this module handles the geometry
lookup, kernel download, texture loading, and figure rendering.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import spiceypy as spice
from PIL import Image

import implanet.ephemeris as eph
from implanet import sun_direction
from implanet.assets import get_kernel, maps_dir
from implanet.figure import plot_planet


REPO = Path(__file__).resolve().parent.parent
DATA = maps_dir()
OUT_DIR = REPO / "examples" / "figures_flyby"
Image.MAX_IMAGE_PIXELS = None


def reproduce_flyby(
    *,
    utc: str,
    body: str,
    body_radius_km: float,
    spacecraft_naif_name: str,
    spacecraft_label: str,
    spk_origin: Optional[str] = None,
    extra_kernels: Sequence[str],
    texture_filename: str,
    output_filename: str,
    grayscale: bool = False,
    ambient: float = 0.04,
    note: str = "",
    refine_ca_hours: Optional[float] = None,
) -> Path:
    """Render the body as seen from the spacecraft at `utc`.

    `spk_origin` overrides the default position origin (which is the
    body name itself) — needed for Pluto/Charon where the system
    barycenter is far from each body's center.

    `refine_ca_hours`: if given, treat `utc` as approximate and scan
    ±this many hours for the true closest-approach time (coarse 60 s
    pass, then 1 s refinement). Robust against published encounter
    times that are rounded or off by a day.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Furnish standard implanet kernels first (leapseconds, PCK, de440s).
    eph.load_kernels()

    # Download (if needed) and furnish extra SPKs for this flyby. Each
    # entry is a kernels.json `id`; implanet.assets handles caching.
    for kid in extra_kernels:
        spice.furnsh(str(get_kernel(kid)))

    iau_frame = f"IAU_{body.upper()}"
    origin = spk_origin if spk_origin is not None else body.upper()

    et = spice.str2et(utc)
    if refine_ca_hours is not None:
        span = refine_ca_hours * 3600.0

        def _dist(e):
            p, _ = spice.spkpos(spacecraft_naif_name, e, "J2000", "NONE",
                                origin)
            return float(np.linalg.norm(p))

        coarse = min(np.arange(et - span, et + span, 60.0), key=_dist)
        et = min(np.arange(coarse - 120.0, coarse + 120.0, 1.0), key=_dist)
        utc = spice.et2utc(et, "ISOC", 0)
        print(f"  refined closest approach → {utc} UTC")

    # Same trick as implanet.ephemeris: compute the position in J2000
    # (no body-center dependency) then rotate into the IAU frame via
    # pxform. Asking spkpos for the IAU frame directly would require
    # SPICE to locate the body center, which is not in de440s.bsp for
    # outer planets.
    pos_j2000, _ = spice.spkpos(spacecraft_naif_name, et, "J2000", "LT", origin)
    R = spice.pxform("J2000", iau_frame, et)
    pos_km = (np.asarray(R, dtype=np.float64)
              @ np.asarray(pos_j2000, dtype=np.float64))
    distance_km = float(np.linalg.norm(pos_km))
    if distance_km == 0.0:
        raise RuntimeError("Zero-length spacecraft position vector.")
    altitude_km = distance_km - body_radius_km
    view = (-pos_km / distance_km).tolist()

    sub_lat = float(np.degrees(np.arcsin(pos_km[2] / distance_km)))
    sub_lon = float(np.degrees(np.arctan2(pos_km[1], pos_km[0])))

    sun = sun_direction(body, utc)

    print(f"  UTC: {utc}")
    print(f"  {spacecraft_label} → {body}")
    print(f"    distance from {body} center: {distance_km:,.1f} km")
    print(f"    altitude (R={body_radius_km:g} km): {altitude_km:,.1f} km")
    print(f"    sub-spacecraft point: ({sub_lat:+.2f}°, {sub_lon:+.2f}°)")
    print(f"    view direction (body-fixed): "
          f"({view[0]:+.4f}, {view[1]:+.4f}, {view[2]:+.4f})")
    print(f"    sun direction (body-fixed):  "
          f"({sun[0]:+.4f}, {sun[1]:+.4f}, {sun[2]:+.4f})")

    tex_path = DATA / texture_filename
    if not tex_path.exists():
        raise SystemExit(f"Missing texture {tex_path}. Run scripts/fetch_maps.py.")

    if grayscale:
        tex = Image.open(tex_path).convert("L").convert("RGB")
    else:
        tex = Image.open(tex_path).convert("RGB")

    title_lines = [f"{spacecraft_label} @ {body}   {utc} UTC"]
    title_lines.append(
        f"sub-s/c ({sub_lat:+.1f}°, {sub_lon:+.1f}°)   "
        f"altitude {altitude_km:,.0f} km"
    )
    if note:
        title_lines.append(note)
    title = "\n".join(title_lines)

    source = "texture: " + tex_path.name + "  •  trajectory: NAIF SPK"

    fig, _ = plot_planet(
        tex,
        view_direction=tuple(view),
        sun_direction=sun,
        ambient=ambient,
        size=900,
        figsize=(7.2, 7.2),
        title=title,
        body_name=body,
        source_text=source,
    )
    out_path = OUT_DIR / output_filename
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"    wrote {out_path}\n")
    return out_path


# -- Kernel aliases ----------------------------------------------------------
# All kernel metadata (URL, size, cache subdir) now lives in
# maps/kernels.json. These names are just the registry `id`s, kept so the
# per-mission scripts read clearly. implanet.assets.get_kernel handles
# the download + caching.

MSGR_SPK = "messenger_cruise"
VGR1_JUP_SPK = "voyager1_jupiter"
VGR1_SAT_SPK = "voyager1_saturn"
VGR2_URA_SPK = "voyager2_uranus"
VGR2_NEP_SPK = "voyager2_neptune"
VGR2_SAT_SPK = "voyager2_saturn"
NH_PLUTO_SPK = "new_horizons_pluto"
DAWN_MARS_SPK = "dawn_cruise"
GLL_CRUISE_SPK = "galileo_cruise"
GLL_TOUR_SPK = "galileo_tour"
JUP_SATELLITES_SPK = "jup_satellites"
NEP_SATELLITES_SPK = "nep_satellites"
