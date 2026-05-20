"""Procedurally generated reference textures.

These are *generated*, not downloaded — manifest entries carry a
``"generator"`` key (and no ``asset_url``); ``get_texture`` builds them
into the maps cache on first use, the same way real maps are fetched.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

# Equirectangular, 2:1. lon0 = -pi by default, so column 0 = lon -180°.
_W, _H = 2048, 1024
_DAY, _NIGHT = 245, 110      # white dayside, GREY shaded side (not black)
_GRID_STEP_DEG = 30.0        # graticule spacing
_GRID_HALF_DEG = 0.5         # half-width of a grid line, in degrees
_GRID_DARK, _GRID_LIGHT = 60, 215  # line tone on light vs grey background


def _grid_mask() -> np.ndarray:
    """(_H, _W) bool: True on a 30° lat/lon graticule line."""
    lon = (np.arange(_W) + 0.5) / _W * 360.0 - 180.0       # -180..180
    lat = 90.0 - (np.arange(_H) + 0.5) / _H * 180.0        # +90..-90

    def _on(deg: np.ndarray) -> np.ndarray:
        m = np.abs((deg + _GRID_STEP_DEG / 2) % _GRID_STEP_DEG
                   - _GRID_STEP_DEG / 2)
        return m <= _GRID_HALF_DEG

    return _on(lon)[None, :] | _on(lat)[:, None]


def _rgb(img: np.ndarray) -> np.ndarray:
    return np.repeat(img[..., None], 3, axis=2).copy()       # (_H, _W, 3)


def _daynight() -> np.ndarray:
    """Hemisphere split with a lat/lon graticule so it reads as a globe.

    White day hemisphere (centred on lon 0 / +X) and a **grey** shaded
    hemisphere (centred on lon ±180) — the shade is grey, not black, so
    the night side stays legible. A 30° graticule is overlaid (dark
    lines on the white side, light lines on the grey side).

    Latitude-independent, so it stays a clean reference for checking
    which hemisphere a `view_direction` shows; the graticule just makes
    the projected disk look three-dimensional. Render it flat (no
    `sun_direction`, or `ambient=1.0`).
    """
    lon = (np.arange(_W) + 0.5) / _W * 360.0 - 180.0       # (_W,)  -180..180

    col = np.full(_W, _NIGHT, dtype=np.uint8)              # grey shade
    col[np.abs(lon) <= 90.0] = _DAY                        # white dayside
    base = np.broadcast_to(col, (_H, _W))

    line_tone = np.where(base >= 180, _GRID_DARK, _GRID_LIGHT).astype(np.uint8)
    img = np.where(_grid_mask(), line_tone, base)
    return _rgb(img)


_GENERATORS = {
    "daynight": _daynight,
}


def build(name: str, dest: Path) -> Path:
    """Generate synthetic texture `name` and write it to `dest`."""
    if name not in _GENERATORS:
        raise KeyError(
            f"Unknown synthetic texture {name!r}. "
            f"Known: {sorted(_GENERATORS)}"
        )
    arr = _GENERATORS[name]()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    fmt = (dest.suffix.lstrip(".") or "png").upper()
    fmt = "JPEG" if fmt in ("JPG", "JPEG") else fmt
    Image.fromarray(arr, mode="RGB").save(tmp, format=fmt)
    tmp.replace(dest)
    return dest
