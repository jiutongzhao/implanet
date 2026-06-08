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

from typing import Optional, Sequence, Union

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


#: Default Sun direction (body-fixed) used by every preset view —
#: prime meridian at the equator. Each camera then sees the same
#: physical illumination from a different angle: "yz" is fully lit
#: (sub-solar = sub-observer), "y" / "-y" / polar views show a clear
#: terminator across the disk, "-yz" sits in the night hemisphere.
_PRESET_DEFAULT_SUN = (1.0, 0.0, 0.0)


def plot_disk(
    texture,
    view_direction: Vec3 = "yz",
    up: Optional[Sequence[float]] = None,
    sun_direction: Optional[Sequence[float]] = None,
    ambient: float = 0.15,
    size: int = 512,
    margin: float = 1.05,
    lon0: float = -np.pi,
    background=None,
    *,
    ax=None,
    show_graticule: bool = True,
    graticule_step_deg: float = 30.0,
    graticule_kwargs: Optional[dict] = None,
    show_limb: bool = True,
    limb_kwargs: Optional[dict] = None,
    show_terminator: bool = True,
    terminator_kwargs: Optional[dict] = None,
    show_subobserver: bool = True,
    subobserver_kwargs: Optional[dict] = None,
    style_axes: Optional[bool] = None,
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
    sun_direction : 3-vector, "off", or None
        Applies Lambertian shading and draws the terminator. The
        default ``None`` lights every preset view from a fixed
        body-fixed Sun at ``(1, 0, 0)`` — prime meridian on the
        equator — so each preset shows the same physical
        illumination from its own viewpoint (``"yz"`` is fully lit,
        ``"-yz"`` falls in the night hemisphere, the perpendicular
        and polar presets see a terminator across the disk). Pass an
        explicit 3-vector to override, or ``"off"`` to disable
        shading entirely. Auto-Sun is skipped when ``view_direction``
        is a free 3-vector.
    ambient, size, lon0, background
        Passed through to :func:`render_disk`.
    margin : float
        Half-width of the data extent — the disk lives in
        ``[-1, +1]`` planet radii and ``margin > 1`` leaves a cushion
        around it for graticule labels or a frame. Drives both the
        ``render_disk`` raster framing and the ``imshow`` extent so
        overlays land in the right place.
    ax : matplotlib Axes or None
        Target axes. ``None`` creates a fresh figure with matplotlib's
        defaults; pass your own pre-styled ``ax`` to control size,
        DPI, title, ticks, etc.
    show_graticule, show_limb, show_terminator, show_subobserver : bool
        Toggle each overlay. The terminator is only drawn when
        ``sun_direction`` is also given.
    graticule_step_deg : float
        Lat/lon step for the graticule.
    *_kwargs : dict or None
        Per-overlay matplotlib kwargs (merged over the defaults).
    style_axes : bool or None
        Whether to set axes limits / aspect / ticks / spines. ``None``
        (the default) means "yes if we created the axes, no if the
        caller passed their own". Set ``True`` / ``False`` to force.
        When ``False``, only the disk image and the overlays are drawn;
        every other axes property is left exactly as you configured it.

    Examples
    --------
    Prime-meridian equator view of Mars with the Sun off to the side::

        from implanet import plot_disk
        fig, ax = plot_disk("Mars", view_direction="yz",
                            sun_direction=(1, 0.4, 0.2))
        fig.savefig("mars.png", dpi=150, bbox_inches="tight")

    Use your own figure if you want a specific size / DPI / title::

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
        plot_disk("Earth", view_direction="xy",
                  sun_direction=(1, 0, 0.4), ax=ax)
        ax.set_title("Earth — north pole")
    """
    import matplotlib.pyplot as plt

    preset_used = isinstance(view_direction, str)
    view_direction, up = resolve_view(view_direction, up)

    # Auto-illuminate the preset views so they don't render flat.
    if sun_direction is None and preset_used:
        sun_direction = _PRESET_DEFAULT_SUN
    elif isinstance(sun_direction, str):
        if sun_direction.lower() in ("off", "none", "flat"):
            sun_direction = None
        else:
            raise ValueError(
                f"sun_direction string {sun_direction!r} not recognised; "
                f"use a 3-vector, None for the auto-Sun, or \"off\"."
            )

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
        fig, ax = plt.subplots()
        owns_axes = True
    else:
        fig = ax.figure
        owns_axes = False
    if style_axes is None:
        style_axes = owns_axes

    if not style_axes:
        # Caller owns the styling — snapshot everything imshow / plot
        # would otherwise autoscale or override, and restore it at the
        # end.
        saved_xlim = ax.get_xlim()
        saved_ylim = ax.get_ylim()
        saved_aspect = ax.get_aspect()
        saved_autoscale = (ax.get_autoscalex_on(), ax.get_autoscaley_on())

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

    if style_axes:
        ax.set_xlim(-margin, margin)
        ax.set_ylim(-margin, margin)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
    else:
        ax.set_xlim(saved_xlim)
        ax.set_ylim(saved_ylim)
        ax.set_aspect(saved_aspect)
        ax.set_autoscalex_on(saved_autoscale[0])
        ax.set_autoscaley_on(saved_autoscale[1])

    return fig, ax
