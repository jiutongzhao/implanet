"""Generate demo figures from the downloaded NASA maps.

Run after `python scripts/fetch_maps.py`; outputs land in examples/figures/.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from implanet import render_planet


REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "maps" / "data"
OUT = REPO / "examples" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def view_from_latlon(lat_deg: float, lon_deg: float):
    """Direction from camera to planet center for an observer over (lat, lon)."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    return (
        -math.cos(lat) * math.cos(lon),
        -math.cos(lat) * math.sin(lon),
        -math.sin(lat),
    )


def sun_from_latlon(lat_deg: float, lon_deg: float):
    """Sun direction (planet -> sun) for a subsolar point at (lat, lon)."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    return (
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    )


def label(img: Image.Image, text: str) -> Image.Image:
    """Draw a small caption in the lower-left corner."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14
        )
    except OSError:
        font = ImageFont.load_default()
    pad = 6
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = pad, img.height - th - pad - 4
    draw.rectangle([x - 4, y - 2, x + tw + 4, y + th + 4], fill=(0, 0, 0, 180))
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    return img


def grid(tiles, cols: int, gap: int = 4, bg=(0, 0, 0)) -> Image.Image:
    rows = math.ceil(len(tiles) / cols)
    w, h = tiles[0].size
    out = Image.new("RGB", (cols * w + (cols - 1) * gap, rows * h + (rows - 1) * gap), bg)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        out.paste(t, (c * (w + gap), r * (h + gap)))
    return out


def fig_earth_rotation(earth: Image.Image, size: int = 320):
    """Earth as if rotating: 6 sub-camera points spaced 60 deg in longitude."""
    sun = sun_from_latlon(15, 30)  # consistent sun for all views
    tiles = []
    for lon in range(0, 360, 60):
        v = view_from_latlon(0, lon)
        img = render_planet(earth, view_direction=v, sun_direction=sun,
                            size=size, ambient=0.08, margin=1.06)
        tiles.append(label(img, f"lon {lon:+d}°"))
    return grid(tiles, cols=3)


def fig_earth_views(earth: Image.Image, size: int = 380):
    """Four distinct vantage points: equator, pole, oblique."""
    sun = sun_from_latlon(20, -40)
    cases = [
        ("equator 0°E", view_from_latlon(0, 0), (0, 0, 1)),
        ("equator 100°E", view_from_latlon(0, 100), (0, 0, 1)),
        ("north pole",     view_from_latlon(85, 0), (1, 0, 0)),
        ("oblique 45°N 60°W", view_from_latlon(45, -60), (0, 0, 1)),
    ]
    tiles = []
    for name, v, up in cases:
        img = render_planet(earth, view_direction=v, up=up,
                            sun_direction=sun, size=size,
                            ambient=0.08, margin=1.06)
        tiles.append(label(img, name))
    return grid(tiles, cols=2)


def fig_earth_terminator(earth: Image.Image, size: int = 340):
    """Same camera; rotate the sun to show day/night terminator."""
    v = view_from_latlon(0, 20)  # camera over Africa
    tiles = []
    for sun_lon in (-90, -30, 30, 90):
        sun = sun_from_latlon(10, sun_lon)
        img = render_planet(earth, view_direction=v, sun_direction=sun,
                            size=size, ambient=0.04, margin=1.06)
        tiles.append(label(img, f"sun lon {sun_lon:+d}°"))
    return grid(tiles, cols=2)


def fig_moon_phases(moon: Image.Image, size: int = 320):
    """Moon at six sun angles — the same view, different illumination."""
    v = view_from_latlon(0, 0)
    tiles = []
    for sun_lon in (-120, -60, 0, 30, 90, 150):
        sun = sun_from_latlon(0, sun_lon)
        img = render_planet(moon, view_direction=v, sun_direction=sun,
                            size=size, ambient=0.02, margin=1.06)
        tiles.append(label(img, f"sun {sun_lon:+d}°"))
    return grid(tiles, cols=3)


def fig_earth_and_moon(earth: Image.Image, moon: Image.Image, size: int = 480):
    """Side-by-side pretty render: Earth + Moon at matched lighting."""
    sun = sun_from_latlon(20, -30)
    e = render_planet(earth, view_direction=view_from_latlon(15, 25),
                      sun_direction=sun, size=size, ambient=0.08, margin=1.05)
    m = render_planet(moon, view_direction=view_from_latlon(0, 10),
                      sun_direction=sun, size=size, ambient=0.03, margin=1.05)
    return grid([label(e, "Earth (NASA Blue Marble)"),
                 label(m, "Moon (NASA SVS / LROC)")], cols=2)


def fig_hires(earth: Image.Image, size: int = 1024):
    """Single high-resolution render to show off detail."""
    sun = sun_from_latlon(25, -50)
    img = render_planet(earth, view_direction=view_from_latlon(20, 0),
                        sun_direction=sun, size=size, ambient=0.06, margin=1.04)
    return label(img, "Earth, 1024 px, 8K source texture")


def main():
    earth_path = DATA / "earth_bluemarble_5400x2700.jpg"
    earth_hires_path = DATA / "earth_land_shallow_topo_8k.tif"
    moon_path = DATA / "moon_lroc_color_2019_4k.tif"

    if not earth_path.exists() or not moon_path.exists():
        raise SystemExit(
            "Missing textures. Run `python scripts/fetch_maps.py` first."
        )

    earth = Image.open(earth_path).convert("RGB")
    moon = Image.open(moon_path).convert("RGB")
    earth_hi = Image.open(earth_hires_path).convert("RGB")

    print("rendering: earth rotation")
    fig_earth_rotation(earth).save(OUT / "01_earth_rotation.png")
    print("rendering: earth viewpoints")
    fig_earth_views(earth).save(OUT / "02_earth_views.png")
    print("rendering: earth terminator")
    fig_earth_terminator(earth).save(OUT / "03_earth_terminator.png")
    print("rendering: moon phases")
    fig_moon_phases(moon).save(OUT / "04_moon_phases.png")
    print("rendering: earth + moon")
    fig_earth_and_moon(earth, moon).save(OUT / "05_earth_and_moon.png")
    print("rendering: high-res earth (8K source)")
    fig_hires(earth_hi).save(OUT / "06_earth_hires.png")

    print(f"\nWrote 6 figures to {OUT}")


if __name__ == "__main__":
    main()
