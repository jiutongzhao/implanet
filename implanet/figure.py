"""Matplotlib figures: planet disk + dashed graticule + scientific axes.

This is an *optional* convenience layer. It is only imported when used,
so matplotlib isn't a hard dependency of the package.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image

from implanet.overlays import (
    flatmap_terminator,
    graticule_segments,
    limb_circle,
    subobserver_point,
    terminator_segments,
)
from implanet.render import render_flatmap, render_disk


Vec3 = Sequence[float]


def plot_planet(
    texture,
    view_direction: Vec3 = (-1.0, 0.0, 0.0),
    up: Vec3 = (0.0, 0.0, 1.0),
    sun_direction: Optional[Vec3] = None,
    ambient: float = 0.1,
    size: int = 720,
    margin: float = 1.08,
    lon0: float = -np.pi,
    *,
    title: Optional[str] = None,
    body_name: Optional[str] = None,
    source_text: Optional[str] = None,
    lat_step_deg: float = 30.0,
    lon_step_deg: float = 30.0,
    graticule_color: str = "0.25",
    graticule_alpha: float = 0.55,
    graticule_lw: float = 0.7,
    show_limb: bool = True,
    show_subobserver: bool = True,
    show_terminator: bool = True,
    terminator_color: str = "white",
    terminator_lw: float = 1.2,
    terminator_ls: str = "--",
    terminator_alpha: float = 0.95,
    figsize: Tuple[float, float] = (6.5, 6.5),
    dpi: int = 150,
    ax=None,
):
    """Render `texture` onto a matplotlib axes with a dashed lat/lon grid.

    The plotted axes range from -1 to +1 in *planet radii* on both axes.
    Returns (fig, ax).

    Examples
    --------
    A publication-style figure: white background, dashed graticule, axis
    ticks in planet radii, sub-observer marker, attribution slot.

        >>> from PIL import Image
        >>> from implanet.figure import plot_planet
        >>> fig, ax = plot_planet(
        ...     Image.open("maps/data/earth_bluemarble_5400x2700.jpg"),
        ...     view_direction=(-1, -0.2, -0.3),
        ...     sun_direction=(1, 0.5, 0.4),
        ...     body_name="Earth",
        ...     source_text="NASA Visible Earth · Blue Marble",
        ... )
        >>> fig.savefig("earth.png", dpi=140, bbox_inches="tight")

    Drive view and sun directly from SPICE for physically-correct
    geometry at a chosen epoch:

        >>> from implanet import sun_direction
        >>> sun = sun_direction("Mars", "2026-05-14T12:00:00")
        >>> fig, _ = plot_planet(mars_tex,
        ...                      view_direction=(-1, 0, 0),
        ...                      sun_direction=sun,
        ...                      title="Mars at 2026-05-14 12:00 UTC")

    Embed multiple variants in a single grid by passing an existing axes:

        >>> fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        >>> plot_planet(blue_marble,      view_direction=v, ax=axes[0])
        >>> plot_planet(visible_clouds,   view_direction=v, ax=axes[1])
    """
    import matplotlib.pyplot as plt

    arr, _, _ = render_disk(
        texture,
        view_direction=view_direction,
        up=up,
        size=size,
        margin=margin,
        lon0=lon0,
        sun_direction=sun_direction,
        ambient=ambient,
        background=(255, 255, 255),
    )

    half = margin
    extent = (-half, half, -half, half)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        fig = ax.figure

    ax.imshow(arr, extent=extent, origin="upper", interpolation="bilinear")

    g = graticule_segments(
        view_direction=view_direction, up=up,
        lat_step_deg=lat_step_deg, lon_step_deg=lon_step_deg,
    )
    for xs, ys in (g["parallels"], g["meridians"]):
        for x, y in zip(xs, ys):
            ax.plot(x, y,
                    linestyle="--", linewidth=graticule_lw,
                    color=graticule_color, alpha=graticule_alpha)

    if show_limb:
        lx, ly = limb_circle()
        ax.plot(lx, ly, linewidth=1.0, color="black")

    if show_terminator and sun_direction is not None:
        txs, tys = terminator_segments(view_direction=view_direction,
                                       sun_direction=sun_direction, up=up)
        for x, y in zip(txs, tys):
            ax.plot(x, y,
                    linewidth=terminator_lw,
                    linestyle=terminator_ls,
                    color=terminator_color,
                    alpha=terminator_alpha)

    if show_subobserver:
        ax.plot(0, 0, marker="+", color="red", markersize=8,
                markeredgewidth=1.2)

    ax.set_xlim(-margin, margin)
    ax.set_ylim(-margin, margin)
    ax.set_aspect("equal")
    ticks = np.arange(-1.0, 1.0001, 0.5)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels([f"{t:+.1f}" for t in ticks])
    ax.set_yticklabels([f"{t:+.1f}" for t in ticks])
    ax.set_xlabel("x  [planet radii]")
    ax.set_ylabel("y  [planet radii]")
    ax.tick_params(direction="out", length=4)

    lat0, lon0_so = subobserver_point(view_direction, up)
    info = f"sub-observer  ({lat0:+.1f}°, {lon0_so:+.1f}°)"
    if sun_direction is not None:
        sun_lat, sun_lon = subobserver_point(
            tuple(-x for x in sun_direction), up
        )
        info += f"     sub-solar  ({sun_lat:+.1f}°, {sun_lon:+.1f}°)"

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    title_text = title or body_name
    if title_text:
        ax.set_title(title_text, fontsize=12, pad=10)

    fig.tight_layout(rect=(0, 0.06, 1, 0.97))
    fig.text(0.5, 0.018, info, ha="center", va="bottom",
             fontsize=8.5, color="0.25")
    if source_text:
        fig.text(0.99, 0.005, source_text, ha="right", va="bottom",
                 fontsize=7, color="0.45")
    return fig, ax


def plot_flatmap(
    texture,
    rotation_lon_deg: float = 0.0,
    sun_direction: Optional[Vec3] = None,
    ambient: float = 0.1,
    lon0: float = -np.pi,
    output_size: Optional[Tuple[int, int]] = None,
    *,
    title: Optional[str] = None,
    body_name: Optional[str] = None,
    source_text: Optional[str] = None,
    lat_step_deg: float = 30.0,
    lon_step_deg: float = 30.0,
    graticule_color: str = "0.25",
    graticule_alpha: float = 0.40,
    graticule_lw: float = 0.6,
    show_terminator: bool = True,
    terminator_color: str = "white",
    terminator_lw: float = 1.2,
    terminator_ls: str = "--",
    terminator_alpha: float = 0.95,
    show_sub_solar: bool = True,
    figsize: Tuple[float, float] = (10.0, 5.4),
    dpi: int = 150,
    ax=None,
):
    """Render `texture` as a plate-carrée map with degree-labeled axes.

    Complements `plot_planet` (which produces an orthographic disk):
    `plot_flatmap` shows the *entire* surface in a rectangular plot,
    with optional `rotation_lon_deg` to shift the body's spin phase and
    optional `sun_direction` to add Lambertian shading + a terminator
    curve. Sub-solar point is marked with a red ``+`` when shading is on.

    Returns (fig, ax).

    Examples
    --------
    A shaded world map at a specific UTC, plus terminator:

        >>> from implanet import sun_direction
        >>> from implanet.figure import plot_flatmap
        >>> sun = sun_direction("Earth", "2026-05-14T12:00:00")
        >>> fig, ax = plot_flatmap(earth_tex, sun_direction=sun,
        ...                        body_name="Earth",
        ...                        title="Earth at 12:00 UTC")
        >>> fig.savefig("earth_flat.png", dpi=140, bbox_inches="tight")
    """
    import matplotlib.pyplot as plt

    arr = render_flatmap(
        texture,
        rotation_lon_deg=rotation_lon_deg,
        sun_direction=sun_direction,
        ambient=ambient,
        lon0=lon0,
        output_size=output_size,
        return_array=True,
    )

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        fig = ax.figure

    extent = (-180.0, 180.0, -90.0, 90.0)
    ax.imshow(arr, extent=extent, origin="upper", interpolation="bilinear",
              aspect="equal")

    # Lat/lon graticule as dashed lines.
    if lat_step_deg > 0:
        for lat in np.arange(-90 + lat_step_deg, 90, lat_step_deg):
            ax.axhline(lat, color=graticule_color, alpha=graticule_alpha,
                       lw=graticule_lw, ls="--")
    if lon_step_deg > 0:
        for lon in np.arange(-180 + lon_step_deg, 180, lon_step_deg):
            ax.axvline(lon, color=graticule_color, alpha=graticule_alpha,
                       lw=graticule_lw, ls="--")

    # Terminator curve.
    sub_solar_str = ""
    if sun_direction is not None:
        if show_terminator:
            txs, tys = flatmap_terminator(sun_direction,
                                          rotation_lon_deg=rotation_lon_deg)
            for x, y in zip(txs, tys):
                ax.plot(x, y,
                        color=terminator_color, lw=terminator_lw,
                        ls=terminator_ls, alpha=terminator_alpha)
        # Sub-solar marker — apply the same display rotation.
        s = np.asarray(sun_direction, dtype=np.float64)
        s = s / np.linalg.norm(s)
        sslat = float(np.degrees(np.arcsin(np.clip(s[2], -1, 1))))
        sslon = float(np.degrees(np.arctan2(s[1], s[0])) - rotation_lon_deg)
        sslon = ((sslon + 180) % 360) - 180
        if show_sub_solar:
            ax.plot(sslon, sslat, marker="+", color="red",
                    markersize=10, markeredgewidth=1.4)
        sub_solar_str = f"   sub-solar  ({sslat:+.1f}°, {sslon:+.1f}°)"

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.set_xticklabels([f"{t:+d}°" for t in np.arange(-180, 181, 60)])
    ax.set_yticklabels([f"{t:+d}°" for t in np.arange(-90, 91, 30)])
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.tick_params(direction="out", length=4)

    fig.patch.set_facecolor("white")
    title_text = title or body_name
    if title_text:
        ax.set_title(title_text + sub_solar_str, fontsize=12, pad=8)
    if source_text:
        fig.text(0.99, 0.005, source_text, ha="right", va="bottom",
                 fontsize=7, color="0.45")
    fig.tight_layout()
    return fig, ax
