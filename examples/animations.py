"""Generate animated GIFs that demonstrate the two transforms the
package controls: viewing direction (FOV) and sun direction.

Three outputs:

* ``earth_rotation.gif``  — camera orbits 360° around Earth at fixed sun
  (FOV sweep, viewing-direction demo).
* ``moon_terminator.gif`` — Moon held fixed, sun direction sweeps 360°
  in longitude (sunlit-direction demo; produces phase-like illumination).
* ``earth_seasons.gif``   — Earth held fixed at the prime meridian,
  SPICE-driven sun direction over one calendar year (real seasonal
  swing of the sub-solar latitude, in 10-day steps).

Each GIF is ~3-4 s at 360x360 px, ~1-3 MB.
"""

from __future__ import annotations

import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Sequence

from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None

from implanet import render_planet, sun_direction, view_direction_from_earth


REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "maps" / "data"
OUT = REPO / "examples" / "animations"
OUT.mkdir(parents=True, exist_ok=True)


def latlon_view(lat_deg: float, lon_deg: float):
    """Camera-to-center direction for an observer over (lat, lon)."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    return (
        -math.cos(lat) * math.cos(lon),
        -math.cos(lat) * math.sin(lon),
        -math.sin(lat),
    )


def latlon_sun(lat_deg: float, lon_deg: float):
    """Planet-to-sun unit vector for a sub-solar point at (lat, lon)."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    return (
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    )


def _font(size: int = 14):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def caption(img: Image.Image, text: str) -> Image.Image:
    out = img.copy()
    draw = ImageDraw.Draw(out)
    font = _font(13)
    pad = 6
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = pad, out.height - th - pad - 4
    draw.rectangle([x - 4, y - 2, x + tw + 4, y + th + 4], fill=(0, 0, 0, 180))
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    return out


def save_gif(frames: List[Image.Image], path: Path, duration_ms: int = 80) -> None:
    """Quantize each frame to an adaptive 256-color palette and write GIF."""
    palette_frames = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
                       for f in frames]
    palette_frames[0].save(
        path,
        save_all=True,
        append_images=palette_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
        disposal=2,
    )


def anim_earth_rotation(size: int = 360, n_frames: int = 36) -> Path:
    """Camera orbits the equator at 10°/frame; sun fixed in body-fixed frame."""
    tex = Image.open(DATA / "earth_bluemarble_5400x2700.jpg").convert("RGB")
    sun = latlon_sun(15, -20)              # fixed in body-fixed coords
    frames: List[Image.Image] = []
    for i in range(n_frames):
        lon = (i * 360 / n_frames) - 180   # sub-observer longitude
        img = render_planet(
            tex, view_direction=latlon_view(15, lon),
            sun_direction=sun, size=size, ambient=0.08, margin=1.06,
            background=(15, 15, 18),
        )
        frames.append(caption(img, f"sub-observer  ({+15.0:+.0f}°, {lon:+6.1f}°)"))
    out = OUT / "earth_rotation.gif"
    save_gif(frames, out, duration_ms=80)
    return out


def anim_moon_terminator(size: int = 360, n_frames: int = 36) -> Path:
    """Moon held fixed; sun sub-point sweeps 360° in longitude."""
    tex = Image.open(DATA / "moon_lroc_color_2019_4k.tif").convert("RGB")
    frames: List[Image.Image] = []
    for i in range(n_frames):
        sun_lon = (i * 360 / n_frames) - 180
        sun = latlon_sun(0, sun_lon)
        img = render_planet(
            tex, view_direction=latlon_view(0, 0),
            sun_direction=sun, size=size, ambient=0.02, margin=1.06,
            background=(8, 8, 12),
        )
        frames.append(caption(img, f"sub-solar  ({0:+.0f}°, {sun_lon:+6.1f}°)"))
    out = OUT / "moon_terminator.gif"
    save_gif(frames, out, duration_ms=85)
    return out


def anim_earth_seasons(size: int = 360, n_days: int = 365, step_days: int = 10) -> Path:
    """Earth held fixed at sub-observer (0°, 0°); real SPICE sun direction
    sampled every `step_days` over one year. Shows the seasonal swing of
    the sub-solar latitude (≈ ±23.4°) and the slight east-west wobble from
    the equation of time."""
    tex = Image.open(DATA / "earth_bluemarble_5400x2700.jpg").convert("RGB")
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    frames: List[Image.Image] = []
    for d in range(0, n_days, step_days):
        dt = base + timedelta(days=d)
        utc = dt.strftime("%Y-%m-%dT%H:%M:%S")
        sun = sun_direction("Earth", utc)
        img = render_planet(
            tex, view_direction=latlon_view(0, 0),
            sun_direction=sun, size=size, ambient=0.08, margin=1.06,
            background=(15, 15, 18),
        )
        frames.append(caption(img, f"{dt.strftime('%Y-%m-%d')}   12:00 UTC"))
    out = OUT / "earth_seasons.gif"
    save_gif(frames, out, duration_ms=110)
    return out


def anim_moon_libration(size: int = 360, n_days: int = 30,
                        step_hours: int = 12) -> Path:
    """The Moon as seen from Earth across one synodic month.

    Both view direction and sun direction come from SPICE:
      * camera = -view_direction_from_earth("Moon", utc)   → captures
        libration (the sub-Earth point swings ±6.7° in lat, ±8° in lon)
      * sun = sun_direction("Moon", utc)                   → captures
        the phase cycle

    This is the "Dial-A-Moon" geometry: same as NASA Goddard SVS's daily
    visualization but at user-chosen sampling.
    """
    tex = Image.open(DATA / "moon_lroc_color_2019_4k.tif").convert("RGB")
    base = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    frames: List[Image.Image] = []
    n_steps = int(n_days * 24 / step_hours)
    for i in range(n_steps):
        dt = base + timedelta(hours=i * step_hours)
        utc = dt.strftime("%Y-%m-%dT%H:%M:%S")
        view_earth = view_direction_from_earth("Moon", utc)
        sun = sun_direction("Moon", utc)
        # camera-to-center = -(Moon->Earth)
        view = tuple(-x for x in view_earth)
        sub_earth_lat = math.degrees(math.asin(max(-1, min(1, view_earth[2]))))
        sub_earth_lon = math.degrees(math.atan2(view_earth[1], view_earth[0]))
        img = render_planet(
            tex, view_direction=view, sun_direction=sun,
            size=size, ambient=0.02, margin=1.08,
            background=(8, 8, 12),
        )
        frames.append(caption(
            img,
            f"{dt:%Y-%m-%d %H:%M UTC}   sub-Earth "
            f"({sub_earth_lat:+5.1f}°, {sub_earth_lon:+6.1f}°)"
        ))
    out = OUT / "moon_libration.gif"
    save_gif(frames, out, duration_ms=80)
    return out


def main():
    print("rendering earth_rotation.gif (camera FOV sweep)")
    p1 = anim_earth_rotation()
    print(f"  → {p1}  ({p1.stat().st_size/1e6:.1f} MB)")

    print("rendering moon_terminator.gif (sun direction sweep)")
    p2 = anim_moon_terminator()
    print(f"  → {p2}  ({p2.stat().st_size/1e6:.1f} MB)")

    print("rendering earth_seasons.gif (SPICE-driven, 1 year)")
    p3 = anim_earth_seasons()
    print(f"  → {p3}  ({p3.stat().st_size/1e6:.1f} MB)")

    print("rendering moon_libration.gif (Earth-view, 1 synodic month)")
    p4 = anim_moon_libration()
    print(f"  → {p4}  ({p4.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
