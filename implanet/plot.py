"""Matplotlib convenience: render a planet disk straight into an axes.

This is an *optional* layer — matplotlib only enters the package when
``plot_disk`` is actually called, so the core renderer keeps its
numpy + Pillow boundary.

``plot_disk`` composes the same primitives most callers reach for by
hand: ``render_disk`` for the raster, then the overlay drawers
(``limb_circle``, ``graticule_segments``, ``disk_terminator``,
``subobserver_point``) on top. It accepts string body names
(``"Mars"``), string preset views (``"yz"`` for the prime meridian,
``"xy"`` for the north pole, etc.), or full 3-vectors.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, Union

import numpy as np

from implanet.overlays import (
    disk_terminator,
    graticule_segments,
    limb_circle,
    subobserver_point,
)
from implanet.projection import resolve_view
from implanet.render import render_disk


Vec3 = Union[Sequence[float], str]


def plot_disk(
    texture,
    view_direction: Vec3 = "yz",
    up: Optional[Sequence[float]] = None,
    sun_direction: Optional[Sequence[float]] = None,
    ambient: float = 0.15,
    size: int = 512,
    margin: float = 1.05,
    lon0: float = -np.pi,
    background="white",
    *,
    ax=None,
    figsize: Tuple[float, float] = (5.5, 5.5),
    dpi: int = 120,
    title: Optional[str] = None,
    show_graticule: bool = True,
    graticule_step_deg: float = 30.0,
    graticule_kwargs: Optional[dict] = None,
    show_limb: bool = True,
    limb_kwargs: Optional[dict] = None,
    show_terminator: bool = True,
    terminator_kwargs: Optional[dict] = None,
    show_subobserver: bool = True,
    subobserver_kwargs: Optional[dict] = None,
    show_axes: bool = False,
):
    """Render a planet disk into a matplotlib axes, with optional overlays.

    Returns ``(fig, ax)``. Calls :func:`render_disk` for the raster and
    composes the package overlay drawers on top; everything stays in the
    unit-disk coordinate frame (data extent
    ``[-margin, margin] × [-margin, margin]``).

    Parameters
    ----------
    texture : str, path, ndarray, or PIL.Image
        Equirectangular map. A bare body name (``"Mars"``) routes through
        the texture registry; a path-looking string is opened directly.
    view_direction : 3-vector or preset name
        Camera→planet direction. Accepts the string presets from
        :func:`resolve_view` — most useful are ``"yz"`` (prime meridian
        equator view, the default), ``"xy"`` (north pole), ``"-xy"``
        (south pole), ``"y"`` / ``"-y"`` (lon = ±90°E equator).
    up : 3-vector or None
        Up hint. ``None`` defers to the preset, or ``(0, 0, 1)`` for a
        free 3-vector ``view_direction``.
    sun_direction : 3-vector or None
        If given, applies Lambertian shading and draws the terminator.
    ambient, size, margin, lon0, background
        Passed through to :func:`render_disk`.
    ax : matplotlib Axes or None
        Target axes. ``None`` creates a fresh figure of ``figsize``/``dpi``.
    title : str or None
        Optional axes title.
    show_graticule, show_limb, show_terminator, show_subobserver : bool
        Toggle each overlay. The terminator is only drawn when
        ``sun_direction`` is also given.
    graticule_step_deg : float
        Lat/lon step for the graticule.
    *_kwargs : dict or None
        Per-overlay matplotlib kwargs (merged over the defaults).
    show_axes : bool
        Show planet-radii tick axes (``True``) or a clean image plate
        (``False``, the default).

    Examples
    --------
    Prime-meridian equator view of Mars with the Sun off to the side::

        from implanet import plot_disk
        fig, ax = plot_disk("Mars", view_direction="yz",
                            sun_direction=(1, 0.4, 0.2))
        fig.savefig("mars.png", dpi=150, bbox_inches="tight")

    North-pole view of Earth — the preset picks an in-plane ``up``::

        fig, ax = plot_disk("Earth", view_direction="xy",
                            sun_direction=(1, 0, 0.4))
    """
    import matplotlib.pyplot as plt

    view_direction, up = resolve_view(view_direction, up)

    img = render_disk(
        texture,
        view_direction=view_direction,
        up=up,
        size=size,
        margin=margin,
        lon0=lon0,
        sun_direction=sun_direction,
        ambient=ambient,
        background=background,
    )

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        fig = ax.figure

    extent = (-margin, margin, -margin, margin)
    cmap = "gray" if img.ndim == 2 else None
    ax.imshow(img, extent=extent, origin="upper", interpolation="bilinear",
              cmap=cmap, vmin=0 if cmap else None, vmax=255 if cmap else None,
              zorder=0)

    if show_graticule:
        gk = {"color": "0.25", "alpha": 0.55, "lw": 0.7, "ls": "--",
              "zorder": 2}
        gk.update(graticule_kwargs or {})
        g = graticule_segments(view_direction, up=up,
                               lat_step_deg=graticule_step_deg,
                               lon_step_deg=graticule_step_deg)
        for key in ("parallels", "meridians"):
            xs, ys = g[key]
            for x, y in zip(xs, ys):
                ax.plot(x, y, **gk)

    if show_limb:
        lk = {"color": "black", "lw": 1.0, "zorder": 3}
        lk.update(limb_kwargs or {})
        x, y = limb_circle(720)
        ax.plot(x, y, **lk)

    if show_terminator and sun_direction is not None:
        tk = {"color": "white", "lw": 1.2, "ls": "--", "zorder": 4}
        tk.update(terminator_kwargs or {})
        xs, ys = disk_terminator(view_direction, sun_direction, up=up)
        for x, y in zip(xs, ys):
            ax.plot(x, y, **tk)

    if show_subobserver:
        sk = {"marker": "+", "color": "red", "ms": 8, "mew": 1.2,
              "ls": "none", "zorder": 5}
        sk.update(subobserver_kwargs or {})
        ax.plot([0], [0], **sk)

    ax.set_xlim(-margin, margin)
    ax.set_ylim(-margin, margin)
    ax.set_aspect("equal")

    if show_axes:
        ticks = np.arange(-1.0, 1.0001, 0.5)
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.set_xticklabels([f"{t:+.1f}" for t in ticks])
        ax.set_yticklabels([f"{t:+.1f}" for t in ticks])
        ax.set_xlabel("x  [planet radii]")
        ax.set_ylabel("y  [planet radii]")
    else:
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)

    if title is not None:
        ax.set_title(title)

    return fig, ax
