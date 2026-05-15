"""Matplotlib figures: planet disk + dashed graticule + scientific axes.

This is an *optional* convenience layer. It is only imported when used,
so matplotlib isn't a hard dependency of the package.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image

from implanet.overlays import graticule_segments, limb_circle, subobserver_point
from implanet.render import render_planet


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

    arr = render_planet(
        texture,
        view_direction=view_direction,
        up=up,
        size=size,
        margin=margin,
        lon0=lon0,
        sun_direction=sun_direction,
        ambient=ambient,
        background=(255, 255, 255),
        return_array=True,
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
    for seg in g["parallels"]:
        ax.plot(seg[:, 0], seg[:, 1],
                linestyle="--", linewidth=graticule_lw,
                color=graticule_color, alpha=graticule_alpha)
    for seg in g["meridians"]:
        ax.plot(seg[:, 0], seg[:, 1],
                linestyle="--", linewidth=graticule_lw,
                color=graticule_color, alpha=graticule_alpha)

    if show_limb:
        c = limb_circle()
        ax.plot(c[:, 0], c[:, 1], linewidth=1.0, color="black")

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
