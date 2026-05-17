"""Render a few views of a synthetic planet (no external assets needed).

Run:  python examples/demo.py
Outputs: demo_front.png, demo_side.png, demo_pole.png, demo_lit.png
"""

import numpy as np
from PIL import Image

from implanet import render_disk


def make_synthetic_texture(h: int = 512, w: int = 1024) -> np.ndarray:
    """Continent-ish blobs + a lat/lon grid, so projections are easy to read."""
    lat = np.linspace(np.pi / 2, -np.pi / 2, h)[:, None]
    lon = np.linspace(-np.pi, np.pi, w)[None, :]

    base = np.zeros((h, w, 3), dtype=np.float64)
    # Ocean.
    base[..., 2] = 120 + 60 * np.cos(lat)

    # A few fake landmasses via summed Gaussians on the sphere.
    centers = [
        (0.4, 0.2, 60, 60),    # lat, lon (rad), color modulation
        (-0.3, 1.6, 80, 40),
        (0.1, -1.8, 50, 70),
        (-0.6, -0.3, 30, 50),
        (1.0, 2.7, 40, 20),
    ]
    land = np.zeros((h, w), dtype=np.float64)
    for clat, clon, _, _ in centers:
        d = (lat - clat) ** 2 + np.minimum(
            (lon - clon) ** 2, (2 * np.pi - np.abs(lon - clon)) ** 2
        )
        land += np.exp(-d * 8.0)
    land_mask = land > 0.4
    base[land_mask] = [90, 140, 70]

    # Polar caps.
    cap = np.abs(np.sin(lat)) > 0.92
    base[np.broadcast_to(cap, base.shape[:2])] = [240, 240, 245]

    # Lat/lon grid lines (every 30 deg).
    lat_grid = (np.abs(((lat * 180 / np.pi) % 30) - 15) > 14.7).repeat(w, axis=1)
    lon_grid = (np.abs(((lon * 180 / np.pi) % 30) - 15) > 14.7).repeat(h, axis=0)
    base[lat_grid | lon_grid] *= 0.6

    return np.clip(base, 0, 255).astype(np.uint8)


def main():
    tex = make_synthetic_texture()
    Image.fromarray(tex).save("demo_texture.png")

    def save(arr, path):
        Image.fromarray(arr).save(path)

    # 1. Looking at lon=0, lat=0 from +X; camera -> center direction is -X.
    arr, _, _ = render_disk(tex, view_direction=(-1, 0, 0), size=512)
    save(arr, "demo_front.png")

    # 2. Side view (90 deg around).
    arr, _, _ = render_disk(tex, view_direction=(0, -1, 0), size=512)
    save(arr, "demo_side.png")

    # 3. Looking down at the north pole.
    arr, _, _ = render_disk(tex, view_direction=(0, 0, -1), up=(1, 0, 0), size=512)
    save(arr, "demo_pole.png")

    # 4. Lit by the sun at (1, 1, 0.3).
    arr, _, _ = render_disk(
        tex,
        view_direction=(-1, -0.2, -0.3),
        sun_direction=(1, 1, 0.3),
        ambient=0.1,
        size=512,
    )
    save(arr, "demo_lit.png")

    print("Wrote demo_texture.png, demo_front.png, demo_side.png, "
          "demo_pole.png, demo_lit.png")


if __name__ == "__main__":
    main()
