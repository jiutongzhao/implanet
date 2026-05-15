"""Projected lat/lon graticules and limb circles for scientific figures.

All output coordinates are in the *unit-disk image plane*: the visible
hemisphere maps into the open disk u**2 + v**2 < 1, with +u to the right
and +v upward. Convert to pixel space with

    (x_px, y_px) = (cx + u * R, cy - v * R)

where R is the disk radius in pixels.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np

from implanet.projection import camera_basis


def _polyline_segments(uvz: np.ndarray, visible: np.ndarray):
    """Break (u, v, z) samples into visible polylines.

    Splits at any sample where visibility changes; for the boundary
    crossing, inserts the exact limb intersection so the line ends on
    u^2 + v^2 = 1.
    """
    n = len(uvz)
    segments: List[np.ndarray] = []
    current: List[Tuple[float, float]] = []
    for i in range(n):
        if visible[i]:
            current.append((uvz[i, 0], uvz[i, 1]))
        if i + 1 < n and visible[i] != visible[i + 1]:
            # Linear interp in (u, v, z) to find z = 0 crossing.
            z0, z1 = uvz[i, 2], uvz[i + 1, 2]
            denom = (z0 - z1)
            if abs(denom) > 1e-12:
                t = z0 / denom
                t = float(np.clip(t, 0.0, 1.0))
                u = uvz[i, 0] + t * (uvz[i + 1, 0] - uvz[i, 0])
                v = uvz[i, 1] + t * (uvz[i + 1, 1] - uvz[i, 1])
                current.append((u, v))
            if current:
                segments.append(np.asarray(current, dtype=np.float64))
                current = []
    if current:
        segments.append(np.asarray(current, dtype=np.float64))
    return [s for s in segments if len(s) >= 2]


def _project(points: np.ndarray, right, up, forward):
    """Return (N, 3) array of (u, v, z_along_forward) per point.

    A point is visible iff z (its component along +forward) is <= 0, since
    the camera sits at -forward * inf and looks toward +forward.
    """
    u = points @ right
    v = points @ up
    z = points @ forward
    return np.stack([u, v, z], axis=-1)


def _parallel_points(lat_rad: float, n: int = 361) -> np.ndarray:
    lon = np.linspace(-np.pi, np.pi, n)
    c = np.cos(lat_rad)
    return np.stack([c * np.cos(lon), c * np.sin(lon),
                     np.full_like(lon, np.sin(lat_rad))], axis=-1)


def _meridian_points(lon_rad: float, n: int = 181) -> np.ndarray:
    lat = np.linspace(-np.pi / 2, np.pi / 2, n)
    c = np.cos(lat)
    return np.stack([c * np.cos(lon_rad), c * np.sin(lon_rad),
                     np.sin(lat)], axis=-1)


def graticule_segments(
    view_direction: Sequence[float],
    up: Sequence[float] = (0.0, 0.0, 1.0),
    lat_step_deg: float = 30.0,
    lon_step_deg: float = 30.0,
    include_poles: bool = True,
    samples_per_line: int = 361,
):
    """Return projected lat/lon line segments for the visible hemisphere.

    Output is a dict with keys "parallels" and "meridians". Each value is
    a list of (M, 2) arrays in unit-disk (u, v) coords; each array is one
    contiguous visible piece of a great/small circle.

    Examples
    --------
    For an equatorial view, the 30° grid produces five parallels and
    twelve meridians:

        >>> g = graticule_segments(view_direction=(-1, 0, 0))
        >>> len(g["parallels"]), len(g["meridians"])
        (5, 12)
        >>> g["meridians"][0].shape          # one polyline segment
        (181, 2)

    Overlay on a matplotlib axes (after `imshow(extent=(-1,1,-1,1))`):

        >>> for seg in g["parallels"] + g["meridians"]:
        ...     ax.plot(seg[:, 0], seg[:, 1], "k--", lw=0.7, alpha=0.55)
    """
    right, up_axis, forward = camera_basis(view_direction, up)

    parallels: List[np.ndarray] = []
    lats = np.arange(-90 + lat_step_deg, 90, lat_step_deg)
    if include_poles:
        # Skip pure poles — they're single points and add no visual info.
        pass
    for lat_deg in lats:
        pts = _parallel_points(np.deg2rad(lat_deg), samples_per_line)
        uvz = _project(pts, right, up_axis, forward)
        visible = uvz[:, 2] <= 1e-9
        parallels.extend(_polyline_segments(uvz, visible))

    meridians: List[np.ndarray] = []
    # Use [0, 360) but recognise -180 == 180 so we don't double-draw.
    lons = np.arange(0, 360, lon_step_deg)
    lons = ((lons + 180) % 360) - 180
    for lon_deg in lons:
        pts = _meridian_points(np.deg2rad(lon_deg), samples_per_line // 2 + 1)
        uvz = _project(pts, right, up_axis, forward)
        visible = uvz[:, 2] <= 1e-9
        meridians.extend(_polyline_segments(uvz, visible))

    # Drop the z column on output.
    return {
        "parallels": [s[:, :2] for s in parallels],
        "meridians": [s[:, :2] for s in meridians],
    }


def _orthonormal_pair_perp_to(v: np.ndarray) -> tuple:
    """Return two unit vectors orthogonal to `v` and to each other."""
    v = v / np.linalg.norm(v)
    # Pick the axis least aligned with v to avoid a near-zero cross product.
    seed = np.array([1.0, 0.0, 0.0]) if abs(v[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = seed - (seed @ v) * v
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(v, e1)
    return e1, e2


def terminator_segments(
    view_direction: Sequence[float],
    sun_direction: Sequence[float],
    up: Sequence[float] = (0.0, 0.0, 1.0),
    samples: int = 361,
):
    """Projected day-night terminator as visible polyline segments.

    The terminator is the great circle of points on the unit sphere
    where the surface is perpendicular to the sun direction (i.e.
    P · sun_unit = 0 — the locus where Lambertian shading drops to zero).
    Only the portion that lies on the visible hemisphere is returned;
    the curve is split into arcs at the limb crossings.

    Returns
    -------
    list of (M, 2) ndarray
        Polyline segments in unit-disk (u, v) coordinates. Plot with
        ``ax.plot(seg[:, 0], seg[:, 1], …)``.

    Examples
    --------
    Sun directly behind the camera produces a full-circle terminator at
    the limb (the planet is fully lit):

        >>> segs = terminator_segments((-1, 0, 0), sun_direction=(1, 0, 0))

    Sun offset 45° produces a half-arc across the disk:

        >>> segs = terminator_segments((-1, 0, 0), sun_direction=(1, 1, 0))
        >>> for seg in segs:
        ...     ax.plot(seg[:, 0], seg[:, 1], color="white",
        ...             lw=1.0, linestyle="--")
    """
    right, up_axis, forward = camera_basis(view_direction, up)
    s = np.asarray(sun_direction, dtype=np.float64)
    s_norm = np.linalg.norm(s)
    if s_norm == 0.0:
        raise ValueError("`sun_direction` must be nonzero.")
    s = s / s_norm

    e1, e2 = _orthonormal_pair_perp_to(s)
    t = np.linspace(0.0, 2.0 * np.pi, samples)
    pts = np.outer(np.cos(t), e1) + np.outer(np.sin(t), e2)   # (N, 3)
    uvz = _project(pts, right, up_axis, forward)
    visible = uvz[:, 2] <= 1e-9
    segs = _polyline_segments(uvz, visible)
    return [s[:, :2] for s in segs]


def limb_circle(samples: int = 360) -> np.ndarray:
    """Return (N, 2) points tracing the unit limb circle.

    Examples
    --------
    Draw the planet outline on top of a rendered disk:

        >>> c = limb_circle(samples=180)
        >>> c.shape
        (181, 2)
        >>> ax.plot(c[:, 0], c[:, 1], "k-", linewidth=1.0)
    """
    t = np.linspace(0, 2 * np.pi, samples + 1)
    return np.stack([np.cos(t), np.sin(t)], axis=-1)


def flatmap_terminator(
    sun_direction: Sequence[float],
    rotation_lon_deg: float = 0.0,
    samples: int = 721,
):
    """Day-night terminator on a plate-carrée flat map.

    Returns the great circle ``{P : P · sun_unit = 0}`` as a sequence of
    polylines in (lon_deg, lat_deg) coordinates suitable for plotting on
    a (-180, 180, -90, 90)-extent matplotlib axes. The curve is split
    wherever it wraps around the ±180° seam.

    `rotation_lon_deg` matches the rotation passed to `render_flatmap`,
    so the terminator stays aligned with the displayed bright spot.

    Examples
    --------
        >>> from implanet import flatmap_terminator
        >>> segs = flatmap_terminator(sun_direction=(1, 0, 0.5))
        >>> for seg in segs:
        ...     ax.plot(seg[:, 0], seg[:, 1], "w--", lw=1.0)
    """
    s = np.asarray(sun_direction, dtype=np.float64)
    n = np.linalg.norm(s)
    if n == 0.0:
        raise ValueError("`sun_direction` must be nonzero.")
    s = s / n

    e1, e2 = _orthonormal_pair_perp_to(s)
    t = np.linspace(0.0, 2.0 * np.pi, samples)
    pts = np.outer(np.cos(t), e1) + np.outer(np.sin(t), e2)
    lat = np.degrees(np.arcsin(np.clip(pts[:, 2], -1.0, 1.0)))
    lon = np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) - rotation_lon_deg
    lon = ((lon + 180.0) % 360.0) - 180.0   # wrap to (-180, 180]

    # Split where the longitude wraps to avoid a horizontal jump.
    dlon = np.abs(np.diff(lon))
    seam = np.where(dlon > 180.0)[0]
    starts = np.concatenate(([0], seam + 1))
    ends = np.concatenate((seam + 1, [len(lon)]))
    segs = []
    for a, b in zip(starts, ends):
        if b - a >= 2:
            segs.append(np.stack([lon[a:b], lat[a:b]], axis=-1))
    return segs


def subobserver_point(
    view_direction: Sequence[float],
    up: Sequence[float] = (0.0, 0.0, 1.0),
):
    """Return (lat_deg, lon_deg) of the sub-camera point on the planet.

    Examples
    --------
    Equator view from the +X side:

        >>> subobserver_point((-1, 0, 0))
        (0.0, 0.0)

    Looking down at the north pole (needs a non-vertical `up`):

        >>> lat, lon = subobserver_point((0, 0, -1), up=(1, 0, 0))
        >>> lat
        90.0
    """
    _, _, forward = camera_basis(view_direction, up)
    # Sub-observer point is the unit-sphere position closest to camera:
    # P = -forward.
    p = -forward
    lat = np.degrees(np.arcsin(np.clip(p[2], -1.0, 1.0)))
    lon = np.degrees(np.arctan2(p[1], p[0]))
    return float(lat), float(lon)
