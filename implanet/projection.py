"""Geometric primitives for projecting a unit sphere into a 2D view.

Conventions
-----------
Planet-fixed frame: right-handed, +Z = north pole, +X intersects the prime
meridian (longitude 0) at the equator, +Y at longitude +90 deg.

A surface point is parameterized by latitude phi in [-pi/2, pi/2] and
longitude lam in [-pi, pi]:

    P = (cos(phi) cos(lam), cos(phi) sin(lam), sin(phi))

Equirectangular textures are laid out with column 0 at lam=-pi (or 0 — see
`lon0`) and row 0 at the north pole.
"""

from __future__ import annotations

import numpy as np


def _normalize(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    if n == 0.0:
        raise ValueError("Cannot normalize a zero-length vector.")
    return v / n


def camera_basis(view_direction, up=(0.0, 0.0, 1.0)):
    """Build an orthonormal camera basis (right, up, forward).

    `view_direction` points from the camera toward the planet center; it
    becomes the +forward axis. `up` is the world-space hint for which way
    is up in the rendered image — it is re-orthogonalized against forward.

    Raises ValueError if `view_direction` and `up` are parallel.
    """
    forward = _normalize(view_direction)
    up_hint = _normalize(up)
    if abs(float(np.dot(forward, up_hint))) > 1.0 - 1e-8:
        raise ValueError("`up` is parallel to `view_direction`; pick another up.")
    right = _normalize(np.cross(forward, up_hint))
    up_axis = np.cross(right, forward)
    return right, up_axis, forward


def orthographic_rays(size, right, up, forward, margin=1.0):
    """Return (points_on_sphere, mask) for an orthographic view.

    Each output pixel (row, col) gets a 3D point on the visible hemisphere
    of the unit sphere (in planet-fixed coordinates) or NaN if the pixel
    lies outside the disk. The mask is True where the pixel hits the sphere.

    `size` is either an int (square image) or (height, width).
    `margin` scales the planet within the image — 1.0 fits the disk exactly.
    """
    if isinstance(size, int):
        h = w = size
    else:
        h, w = size
    radius = 0.5 * min(h, w) / margin

    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    ys = np.arange(h, dtype=np.float64)[:, None]
    xs = np.arange(w, dtype=np.float64)[None, :]

    # Normalized image-plane coordinates: u right, v up, image-y points down.
    u = (xs - cx) / radius
    v = -(ys - cy) / radius

    r2 = u * u + v * v
    mask = r2 <= 1.0
    z = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))  # depth toward camera

    # Point on near hemisphere: P = u*right + v*up - z*forward.
    points = (
        u[..., None] * right
        + v[..., None] * up
        - z[..., None] * forward
    )
    points = np.where(mask[..., None], points, np.nan)
    return points, mask


def sphere_to_uv(points, lon0=0.0):
    """Map points on the unit sphere to equirectangular (u, v) in [0, 1].

    `lon0` is the longitude (radians) of the texture's left edge.
    """
    x = points[..., 0]
    y = points[..., 1]
    z = np.clip(points[..., 2], -1.0, 1.0)

    lat = np.arcsin(z)                       # [-pi/2, pi/2]
    lon = np.arctan2(y, x)                   # [-pi, pi]

    u = ((lon - lon0) / (2.0 * np.pi)) % 1.0
    v = 0.5 - lat / np.pi                    # 0 at north pole, 1 at south
    return u, v
