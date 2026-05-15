"""High-level rendering of a planet view from an equirectangular texture."""

from __future__ import annotations

from typing import Sequence, Tuple, Union

import numpy as np
from PIL import Image

from implanet.projection import camera_basis, orthographic_rays, sphere_to_uv


ArrayLike = Union[np.ndarray, "Image.Image"]
Vec3 = Sequence[float]


def _as_texture_array(texture: ArrayLike) -> np.ndarray:
    if isinstance(texture, Image.Image):
        texture = np.asarray(texture)
    tex = np.asarray(texture)
    if tex.ndim == 2:
        tex = tex[..., None]
    elif tex.ndim != 3:
        raise ValueError("Texture must be 2D (HxW) or 3D (HxWxC).")
    return tex


def _sample_bilinear(texture: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Bilinear sample with wraparound in u, clamp in v."""
    h, w, c = texture.shape

    # Pixel-center sampling: texture[0,0] sits at u=0.5/w, v=0.5/h.
    fx = u * w - 0.5
    fy = v * h - 0.5

    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    tx = (fx - x0)[..., None]
    ty = (fy - y0)[..., None]

    x1 = x0 + 1
    y1 = y0 + 1

    x0w = np.mod(x0, w)
    x1w = np.mod(x1, w)
    y0c = np.clip(y0, 0, h - 1)
    y1c = np.clip(y1, 0, h - 1)

    c00 = texture[y0c, x0w]
    c10 = texture[y0c, x1w]
    c01 = texture[y1c, x0w]
    c11 = texture[y1c, x1w]

    top = c00 * (1.0 - tx) + c10 * tx
    bot = c01 * (1.0 - tx) + c11 * tx
    return top * (1.0 - ty) + bot * ty


def render_planet(
    texture: ArrayLike,
    view_direction: Vec3 = (1.0, 0.0, 0.0),
    up: Vec3 = (0.0, 0.0, 1.0),
    size: Union[int, Tuple[int, int]] = 512,
    margin: float = 1.05,
    lon0: float = -np.pi,
    sun_direction: Vec3 | None = None,
    ambient: float = 0.15,
    background: Sequence[int] = (0, 0, 0),
    return_array: bool = False,
):
    """Render an equirectangular planet map as viewed from `view_direction`.

    Parameters
    ----------
    texture : ndarray or PIL.Image
        Equirectangular map. Width spans longitude over 2*pi, height spans
        latitude over pi. Row 0 is the north pole.
    view_direction : 3-vector
        Direction from the camera toward the planet center, in planet-fixed
        coordinates. Need not be unit length.
    up : 3-vector
        World-space "up" hint. Defaults to the north pole (+Z).
    size : int or (height, width)
        Output image size. An int produces a square image.
    margin : float
        Padding around the planet disk. 1.0 = disk touches the shorter edge.
    lon0 : float
        Longitude (radians) corresponding to the texture's left edge. The
        default (-pi) means column 0 is at lon=-180 deg. Use 0.0 if your
        texture starts at the prime meridian.
    sun_direction : 3-vector or None
        If given, applies Lambertian shading. The vector points FROM the
        planet TOWARD the sun (in planet-fixed coordinates).
    ambient : float
        Ambient light term in [0, 1] used when `sun_direction` is set.
    background : 3-tuple of uint8
        RGB fill for pixels outside the planet disk.
    return_array : bool
        If True, return a NumPy uint8 array instead of a PIL.Image.
    """
    tex = _as_texture_array(texture)
    tex_f = tex.astype(np.float64)

    right, up_axis, forward = camera_basis(view_direction, up)
    points, mask = orthographic_rays(size, right, up_axis, forward, margin=margin)

    # Sample texture at every pixel (mask is applied at the end).
    safe_points = np.where(np.isnan(points), 0.0, points)
    u, v = sphere_to_uv(safe_points, lon0=lon0)
    sampled = _sample_bilinear(tex_f, u, v)  # (H, W, C)

    if sun_direction is not None:
        sun = np.asarray(sun_direction, dtype=np.float64)
        sun_norm = np.linalg.norm(sun)
        if sun_norm == 0.0:
            raise ValueError("`sun_direction` must be nonzero.")
        sun = sun / sun_norm
        # Surface normal at a point on the unit sphere equals the point itself.
        cos_i = np.clip(np.einsum("...i,i->...", safe_points, sun), 0.0, 1.0)
        shade = ambient + (1.0 - ambient) * cos_i
        sampled = sampled * shade[..., None]

    out = np.empty_like(sampled)
    bg = np.asarray(background, dtype=np.float64)
    if sampled.shape[-1] == 1:
        bg = np.array([bg.mean()])
    elif sampled.shape[-1] == 4:
        bg = np.concatenate([bg[:3], [0.0]])  # transparent background
    elif sampled.shape[-1] != 3:
        bg = np.zeros(sampled.shape[-1])

    out[...] = bg
    out = np.where(mask[..., None], sampled, out)
    out = np.clip(out, 0.0, 255.0).astype(np.uint8)

    if out.shape[-1] == 1:
        out = out[..., 0]

    if return_array:
        return out
    mode = {1: "L", 2: "LA", 3: "RGB", 4: "RGBA"}.get(
        out.shape[-1] if out.ndim == 3 else 1, "RGB"
    )
    return Image.fromarray(out, mode=mode)
