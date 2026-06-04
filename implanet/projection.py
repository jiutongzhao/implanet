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


# Named preset views: ``(view_direction, default_up)`` per name. The
# camera sits on the named (signed) axis and looks at the origin; ``view``
# is the camera→planet vector, so for camera on +X it points to -X. The
# plane-named aliases ("XY", "XZ", "YZ") choose the positive-side camera
# by convention. See `resolve_view` for the API.
_VIEW_PRESETS = {
    # ── single-axis presets (camera on signed axis) ──────────────────
    "x":   ((-1.0,  0.0,  0.0), (0.0, 0.0, 1.0)),   # camera on +X (sub-obs at prime meridian)
    "-x":  (( 1.0,  0.0,  0.0), (0.0, 0.0, 1.0)),   # camera on -X (sub-obs at lon=180°)
    "y":   (( 0.0, -1.0,  0.0), (0.0, 0.0, 1.0)),   # camera on +Y (sub-obs at lon=+90°E)
    "-y":  (( 0.0,  1.0,  0.0), (0.0, 0.0, 1.0)),   # camera on -Y (sub-obs at lon=-90°E)
    "z":   (( 0.0,  0.0, -1.0), (0.0, 1.0, 0.0)),   # camera on +Z (north-pole view)
    "-z":  (( 0.0,  0.0,  1.0), (0.0, 1.0, 0.0)),   # camera on -Z (south-pole view)
    # ── plane-named aliases ──────────────────────────────────────────
    "xy":  (( 0.0,  0.0, -1.0), (0.0, 1.0, 0.0)),   # ≡ +Z (top-down on XY plane)
    "-xy": (( 0.0,  0.0,  1.0), (0.0, 1.0, 0.0)),   # ≡ -Z
    "xz":  (( 0.0, -1.0,  0.0), (0.0, 0.0, 1.0)),   # ≡ +Y (XZ plane from +Y side)
    "-xz": (( 0.0,  1.0,  0.0), (0.0, 0.0, 1.0)),   # ≡ -Y
    "yz":  ((-1.0,  0.0,  0.0), (0.0, 0.0, 1.0)),   # ≡ +X (the classic equator view)
    "-yz": (( 1.0,  0.0,  0.0), (0.0, 0.0, 1.0)),   # ≡ -X
}


def resolve_view(view, up=None):
    """Resolve a `view` argument into an explicit ``(view_direction, up)``.

    Accepts either a 3-vector (returned as-is, with ``up`` defaulted to
    ``(0, 0, 1)`` if None) or one of the preset names:

      ``"x" / "-x" / "y" / "-y" / "z" / "-z"``
        Camera on the named signed axis, looking at the origin.
      ``"xy" / "-xy"``
        Top-down (north pole) / bottom-up (south pole) view.
      ``"xz" / "-xz"``
        Side view of the XZ plane from the +Y / -Y side.
      ``"yz" / "-yz"``
        Side view of the YZ plane from the +X / -X side. ``"yz"`` is
        the classic prime-meridian equator view.

    A leading ``+`` is accepted (``"+xy"`` ≡ ``"xy"``). Names are case-
    insensitive. If ``up`` is None and ``view`` is a preset, the preset's
    own up vector is returned (necessary for polar presets where the
    default ``(0, 0, 1)`` would be parallel to the forward axis). An
    explicit ``up`` always wins.

    Examples
    --------
        >>> resolve_view("YZ")              # classic equator, lon=0 centre
        ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        >>> resolve_view("z")               # north-pole view
        ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0))
        >>> resolve_view((1, 0, 0))         # 3-vector passes through
        ((1, 0, 0), (0.0, 0.0, 1.0))
    """
    if isinstance(view, str):
        key = view.strip().lower().lstrip("+")
        if key not in _VIEW_PRESETS:
            raise ValueError(
                f"Unknown view preset {view!r}. Known presets: "
                + ", ".join(sorted(_VIEW_PRESETS))
            )
        vd, default_up = _VIEW_PRESETS[key]
        return vd, (tuple(up) if up is not None else default_up)
    return view, ((0.0, 0.0, 1.0) if up is None else up)


def camera_basis(view_direction, up=(0.0, 0.0, 1.0)):
    """Build an orthonormal camera basis (right, up, forward).

    `view_direction` points from the camera toward the planet center; it
    becomes the +forward axis. `up` is the world-space hint for which way
    is up in the rendered image — it is re-orthogonalized against forward.

    Raises ValueError if `view_direction` and `up` are parallel.

    Examples
    --------
    Looking at the planet from the +X direction (sub-observer point at
    lat=0, lon=0):

        >>> right, up, forward = camera_basis((-1, 0, 0))
        >>> forward                    # camera looks along -X toward origin
        array([-1.,  0.,  0.])
        >>> up                         # equator-aligned view, +Z stays up
        array([0., 0., 1.])

    A polar view requires a non-vertical `up` hint:

        >>> r, u, f = camera_basis((0, 0, -1), up=(1, 0, 0))
        >>> f                          # looking down at the north pole
        array([ 0.,  0., -1.])
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

    Examples
    --------
    Trace the visible hemisphere for a 256x256 render from the +X side:

        >>> r, u, f = camera_basis((-1, 0, 0))
        >>> points, mask = orthographic_rays(256, r, u, f)
        >>> mask.shape
        (256, 256)
        >>> abs(mask.mean() - 3.14159/4) < 0.01    # disk area = pi*R^2
        True
        >>> points[128, 128]            # center pixel hits sub-observer point
        array([1., 0., 0.])

    Pixels outside the disk are NaN:

        >>> bool(np.isnan(points[0, 0, 0]))
        True
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

    Examples
    --------
    Spot-check the texture coordinate at famous points on the sphere:

        >>> import numpy as np
        >>> p = np.array([[1, 0, 0],     # prime meridian, equator
        ...               [0, 1, 0],     # 90° east, equator
        ...               [0, 0, 1],     # north pole
        ...               [0, 0, -1]])   # south pole
        >>> u, v = sphere_to_uv(p, lon0=-np.pi)
        >>> u
        array([0.5 , 0.75, 0.  , 0.  ])
        >>> v
        array([0.5, 0.5, 0. , 1. ])

    For a texture whose left edge sits at the prime meridian, pass
    ``lon0=0`` instead.
    """
    x = points[..., 0]
    y = points[..., 1]
    z = np.clip(points[..., 2], -1.0, 1.0)

    lat = np.arcsin(z)                       # [-pi/2, pi/2]
    lon = np.arctan2(y, x)                   # [-pi, pi]

    u = ((lon - lon0) / (2.0 * np.pi)) % 1.0
    v = 0.5 - lat / np.pi                    # 0 at north pole, 1 at south
    return u, v
