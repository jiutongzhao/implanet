"""Shared publication style for the implanet figure series (``examples/nature/``).

Every plate in this folder is an *image-plate* figure: raster planet disks
(or flat maps) rendered by ``implanet``, with **editable vector overlays**
(graticules, the day/night terminator, sub-point markers) and **editable
text** drawn on top by matplotlib. The disks sit on a uniform near-black
axes facecolor so the limb reads cleanly and no white halo rings the edge.

The module centralises:

* ``apply_style()``       — Nature-leaning rcParams; editable SVG text.
* a restrained palette    — one neutral family, one signal family (gold =
                            the Sun cue), one accent (cyan = the observer).
* disk-axes helpers       — ``disk_ax``, ``show_disk`` (consistent extent),
                            and the overlay drawers that wrap the real
                            ``implanet`` overlay functions.
* ``finalize()``          — saves ``.png`` (300 dpi) + ``.pdf`` + ``.svg``.

Nothing here renders pixels itself; it only composes ``implanet`` output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")  # headless / batch
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Some catalogued USGS/DLR mosaics are larger than PIL's decompression-bomb
# guard; the registry is trusted, so lift the cap for these example renders.
Image.MAX_IMAGE_PIXELS = None

from implanet import (
    disk_terminator,
    flatmap_terminator,
    graticule_segments,
    limb_circle,
    subobserver_point,
)

# ── Output location ───────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO / "figures" / "nature"

# ── Palette ───────────────────────────────────────────────────────────────
# Disks are dark image plates, so overlays are light. Gold is the Sun cue
# (terminator + sub-solar point); cyan is the observer cue (sub-observer).
PLATE_BG = "#121212"          # axes facecolor == render_disk background
GRID = "#FFFFFF"              # graticule (low alpha)
LIMB = "#FFFFFF"              # planet outline
SUN = "#FFD54A"              # terminator + sub-solar marker
OBS = "#27C7E0"              # sub-observer marker
INK = "#1A1A1A"              # page text
MUTED = "#6E6E6E"            # captions / secondary text


def apply_style(font_size: float = 8.0) -> None:
    """Nature-leaning rcParams. Editable SVG text is mandatory and first."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
    plt.rcParams["svg.fonttype"] = "none"   # keep <text> nodes, not paths
    plt.rcParams["pdf.fonttype"] = 42        # editable TrueType in PDF
    plt.rcParams["font.size"] = font_size
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["axes.titlesize"] = font_size + 0.5
    plt.rcParams["axes.labelsize"] = font_size
    plt.rcParams["xtick.labelsize"] = font_size - 1
    plt.rcParams["ytick.labelsize"] = font_size - 1
    plt.rcParams["legend.frameon"] = False
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["savefig.facecolor"] = "white"


# ── Disk axes ─────────────────────────────────────────────────────────────
def disk_ax(ax, title: str | None = None) -> None:
    """Style an axes that holds a rendered planet disk (image plate)."""
    ax.set_facecolor(PLATE_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    for s in ax.spines.values():
        s.set_visible(False)
    if title:
        ax.set_title(title, color=INK, pad=4)


def show_disk(ax, img: np.ndarray, margin: float = 1.0):
    """imshow a ``render_disk`` result with the exact unit-disk extent.

    Overlay coordinates from ``implanet`` are in unit-disk space
    (u, v in [-1, 1]); plotting them in these data coordinates lands them
    on the disk regardless of `margin`.
    """
    cmap = "gray" if img.ndim == 2 else None
    ax.imshow(img, extent=(-margin, margin, -margin, margin), origin="upper",
              cmap=cmap, vmin=0, vmax=255, interpolation="bilinear", zorder=0)
    ax.set_xlim(-margin, margin)
    ax.set_ylim(-margin, margin)


# ── Overlays (wrap the real implanet functions) ───────────────────────────
def draw_graticule(ax, view, up=(0, 0, 1), step=30.0, color=GRID, alpha=0.32,
                   lw=0.5):
    g = graticule_segments(view, up=up, lat_step_deg=step, lon_step_deg=step)
    for key in ("parallels", "meridians"):
        xs, ys = g[key]
        for x, y in zip(xs, ys):
            ax.plot(x, y, color=color, lw=lw, alpha=alpha, zorder=2)


def draw_limb(ax, color=LIMB, alpha=0.55, lw=0.8):
    x, y = limb_circle(720)
    ax.plot(x, y, color=color, lw=lw, alpha=alpha, zorder=3)


def draw_terminator(ax, view, sun, up=(0, 0, 1), color=SUN, lw=1.4):
    xs, ys = disk_terminator(view, sun, up=up)
    for x, y in zip(xs, ys):
        ax.plot(x, y, color=color, lw=lw, zorder=4)


def mark_subobserver(ax, view, up=(0, 0, 1), color=OBS, label=True):
    """A small cross at the sub-observer point — always the disk centre."""
    ax.plot(0, 0, marker="+", color=color, ms=7, mew=1.6, zorder=5)
    if label:
        lat, lon = subobserver_point(view, up)
        ax.text(0.04, -0.04, _fmt(lat, lon), color=color, fontsize=6,
                ha="left", va="top", zorder=5)


def mark_subsolar(ax, view, sun, up=(0, 0, 1), color=SUN):
    """Project the sub-solar point (the Sun direction on the sphere) and,
    if it lies on the visible hemisphere, mark it with a star."""
    from implanet import camera_basis
    right, up_axis, forward = camera_basis(view, up)
    s = np.asarray(sun, float)
    s = s / np.linalg.norm(s)
    u, v, z = s @ right, s @ up_axis, s @ forward
    if z <= 1e-9:  # visible hemisphere
        ax.plot(u, v, marker="*", color=color, ms=9, mec="white", mew=0.5,
                zorder=6)


def panel_label(ax, text, color="white", x=0.03, y=0.97):
    ax.text(x, y, text, transform=ax.transAxes, color=color, fontsize=10,
            fontweight="bold", ha="left", va="top", zorder=7)


# ── Flat-map overlay ──────────────────────────────────────────────────────
def draw_flatmap_terminator(ax, sun, rotation_lon_deg=0.0, color=SUN, lw=1.6):
    xs, ys = flatmap_terminator(sun, rotation_lon_deg=rotation_lon_deg)
    for x, y in zip(xs, ys):
        ax.plot(x, y, color=color, lw=lw, zorder=4)


# ── Formatting + save ─────────────────────────────────────────────────────
def _fmt(lat: float, lon: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.0f}°{ns} {abs(lon):.0f}°{ew}"


def caption(fig, text: str, y: float = 0.012):
    fig.text(0.5, y, text, ha="center", va="bottom", color=MUTED,
             fontsize=6.2, wrap=True)


def finalize(fig, stem: str, formats=("png", "pdf", "svg"), dpi: int = 300,
             png_dpi: int = 200):
    """Save editable PDF/SVG masters (300 dpi) plus a lighter PNG preview.

    The ``.pdf``/``.svg`` keep text editable for figure assembly; the
    ``.png`` is the markdown-displayable preview and is gitignored-friendly
    at ``png_dpi`` (the masters regenerate from the script).
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    for fmt in formats:
        p = OUT_DIR / f"{stem}.{fmt}"
        fig.savefig(p, dpi=(png_dpi if fmt == "png" else dpi),
                    bbox_inches="tight", facecolor="white")
        saved.append(p)
    plt.close(fig)
    return saved
