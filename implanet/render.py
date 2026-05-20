"""High-level rendering of a planet view from an equirectangular texture."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence, Tuple, Union

import numpy as np
from PIL import Image

from implanet.projection import camera_basis, orthographic_rays, sphere_to_uv


ArrayLike = Union[np.ndarray, "Image.Image", str, "os.PathLike"]
Vec3 = Sequence[float]


def _as_texture_array(texture: ArrayLike) -> np.ndarray:
    # A path (str / Path) is opened with Pillow, which picks the decoder
    # from the file's conventional type (.png/.jpg/.tif/...).
    if isinstance(texture, (str, os.PathLike)):
        texture = Image.open(texture)
    if isinstance(texture, Image.Image):
        # Renderer handles 1/3/4-channel arrays; coerce palette, CMYK,
        # YCbCr, etc. to RGB so samples are real colours, not indices.
        if texture.mode not in ("L", "RGB", "RGBA"):
            texture = texture.convert("RGB")
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


def render_disk(
    texture: ArrayLike,
    view_direction: Vec3 = (1.0, 0.0, 0.0),
    up: Vec3 = (0.0, 0.0, 1.0),
    size: Union[int, Tuple[int, int]] = 512,
    margin: float = 1.05,
    lon0: float = -np.pi,
    sun_direction: Vec3 | None = None,
    ambient: float = 0.15,
    background: Sequence[int] = (0, 0, 0),
):
    """Render an equirectangular planet map as viewed from `view_direction`.

    Returns
    -------
    image : ndarray, uint8
        Rendered disk, shape (H, W) for grayscale or (H, W, C) for color.
        Row 0 is the top of the image (image-space convention). The disk
        occupies ``[-1, +1]`` planet radii on both axes; off-disk pixels
        are filled with `background` (or transparent for RGBA textures).
        To plot with `matplotlib.imshow`, use
        ``extent=(-margin, +margin, -margin, +margin)``.

    Parameters
    ----------
    texture : str, path, ndarray, or PIL.Image
        Equirectangular map. Width spans longitude over 2*pi, height spans
        latitude over pi. Row 0 is the north pole. A str/Path is opened
        with Pillow (decoder chosen from the file's conventional type).
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

    Examples
    --------
    Render the sub-observer hemisphere and save with PIL (pass the
    texture path straight in — no need to open it yourself):

        >>> from PIL import Image
        >>> img = render_disk("maps/data/earth_bluemarble_5400x2700.jpg",
        ...                   view_direction=(-1, 0, 0), size=400)
        >>> Image.fromarray(img).save("earth.png")

    Plot with matplotlib `imshow` — the disk lands at [-1, +1] on both
    axes, with a small `margin` cushion around it:

        >>> import matplotlib.pyplot as plt
        >>> img = render_disk(tex, view_direction=(-1, 0, 0),
        ...                   sun_direction=(1, 0, 0), margin=1.05)
        >>> fig, ax = plt.subplots()
        >>> ax.imshow(img, extent=(-1.05, 1.05, -1.05, 1.05))
        >>> ax.set_aspect("equal")

    Use SPICE for both vectors:

        >>> from implanet import sun_direction
        >>> sun = sun_direction("Mars", "2026-05-14T12:00:00")
        >>> img = render_disk(mars_tex,
        ...                   view_direction=(-1, 0, 0),
        ...                   sun_direction=sun)
        >>> img.shape, img.dtype
        ((512, 512, 3), dtype('uint8'))
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
    return out


def render_flatmap(
    texture: ArrayLike,
    rotation_lon_deg: float = 0.0,
    sun_direction: Vec3 | None = None,
    ambient: float = 0.15,
    lon0: float = -np.pi,
    output_size: Union[None, Tuple[int, int]] = None,
    return_array: bool = False,
):
    """Render the texture as a flat 2:1 equirectangular map.

    Unlike `render_disk`, which produces an orthographic disk view of
    the visible hemisphere, this function returns a full surface map in
    plate-carrée projection (longitude on the x-axis, latitude on the
    y-axis, both linear). Two optional transforms are applied per pixel:

    * **Rotation** — `rotation_lon_deg` shifts the body's spin phase. The
      pixel at output longitude ``λ_disp`` corresponds to body-fixed
      longitude ``λ_disp + rotation_lon_deg``, so increasing the rotation
      *rolls the map westward* (sub-solar bright spot moves east in
      display). Use this to animate one rotation period.

    * **Shadow** — if `sun_direction` (planet → Sun, body-fixed) is
      given, each pixel is multiplied by
      ``ambient + (1 − ambient) · max(0, P · sun_unit)`` where ``P`` is
      the unit-sphere position at that pixel. The night side fades to
      `ambient`; the sub-solar point is full bright.

    Parameters
    ----------
    texture : str, path, ndarray, or PIL.Image
        Source equirectangular map (2:1). A str/Path is opened with
        Pillow (decoder chosen from the file's conventional type).
    rotation_lon_deg : float
        Display rotation in degrees, in [−360, +360].
    sun_direction : 3-vector or None
        Body-fixed planet→Sun direction. Omit to skip shading.
    ambient : float
        Floor on the cosine factor, in [0, 1].
    lon0 : float
        Longitude (radians) corresponding to texture column 0.
    output_size : (height, width) or None
        Output dimensions. If None, matches the texture (must be 2:1 to
        avoid distortion).
    return_array : bool
        True → np.uint8 array; False → PIL.Image.

    Examples
    --------
    A plain shaded world map at the current SPICE epoch:

        >>> from implanet import sun_direction, render_flatmap
        >>> from PIL import Image
        >>> tex = Image.open("maps/data/earth_bluemarble_5400x2700.jpg")
        >>> sun = sun_direction("Earth", "2026-05-14T12:00:00")
        >>> img = render_flatmap(tex, sun_direction=sun, ambient=0.05)

    Spin Earth under a fixed sun (frames for an animation):

        >>> frames = [render_flatmap(tex, rotation_lon_deg=d,
        ...                          sun_direction=sun, ambient=0.05)
        ...           for d in range(0, 360, 10)]
    """
    tex = _as_texture_array(texture)
    tex_f = tex.astype(np.float64)
    th, tw = tex.shape[:2]

    if output_size is None:
        oh, ow = th, tw
    else:
        oh, ow = output_size

    # Output pixel grid → (lat_disp, lon_disp), with pixel centers at
    # (j + 0.5, i + 0.5) so the top row sits at lat = +pi/2 - half-step.
    j = np.arange(oh, dtype=np.float64)[:, None]
    i = np.arange(ow, dtype=np.float64)[None, :]
    lat_disp = (0.5 - (j + 0.5) / oh) * np.pi          # [+π/2, −π/2]
    lon_disp = ((i + 0.5) / ow - 0.5) * 2 * np.pi      # [−π, +π)

    # Apply body-spin rotation. The texture (and the surface normal used
    # for shading) live in the rotated body-fixed frame.
    lat_body = np.broadcast_to(lat_disp, (oh, ow))
    lon_body = np.broadcast_to(lon_disp, (oh, ow)) + np.radians(rotation_lon_deg)

    # Texture coords: wrap in longitude, clamp in latitude.
    u = ((lon_body - lon0) / (2.0 * np.pi)) % 1.0
    v = 0.5 - lat_body / np.pi
    sampled = _sample_bilinear(tex_f, u, v)

    if sun_direction is not None:
        sun = np.asarray(sun_direction, dtype=np.float64)
        sun_norm = np.linalg.norm(sun)
        if sun_norm == 0.0:
            raise ValueError("`sun_direction` must be nonzero.")
        sun = sun / sun_norm

        cl = np.cos(lat_body); sl = np.sin(lat_body)
        co = np.cos(lon_body); so = np.sin(lon_body)
        # Body-fixed surface point P (== outward normal on a unit sphere).
        cos_i = cl * (co * sun[0] + so * sun[1]) + sl * sun[2]
        cos_i = np.clip(cos_i, 0.0, 1.0)
        shade = ambient + (1.0 - ambient) * cos_i
        sampled = sampled * shade[..., None]

    out = np.clip(sampled, 0.0, 255.0).astype(np.uint8)
    if out.shape[-1] == 1:
        out = out[..., 0]

    if return_array:
        return out
    mode = {1: "L", 2: "LA", 3: "RGB", 4: "RGBA"}.get(
        out.shape[-1] if out.ndim == 3 else 1, "RGB"
    )
    return Image.fromarray(out, mode=mode)
