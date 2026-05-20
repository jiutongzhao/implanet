"""Smoke + geometric correctness tests for implanet."""

import numpy as np
import pytest

from implanet import (
    render_disk, render_flatmap,
    camera_basis, sphere_to_uv,
    terminator_segments, flatmap_terminator,
)
from implanet.projection import orthographic_rays


def test_camera_basis_orthonormal():
    r, u, f = camera_basis((1, 0, 0))
    M = np.stack([r, u, f])
    np.testing.assert_allclose(M @ M.T, np.eye(3), atol=1e-12)


def test_camera_basis_rejects_parallel_up():
    with pytest.raises(ValueError):
        camera_basis((0, 0, 1), up=(0, 0, 1))


def test_orthographic_disk_is_unit_sphere():
    r, u, f = camera_basis((1, 0, 0))
    pts, mask = orthographic_rays(64, r, u, f, margin=1.0)
    norms = np.linalg.norm(pts[mask], axis=-1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-12)


def test_orthographic_disk_area_matches_pi_r2():
    r, u, f = camera_basis((1, 0, 0))
    _, mask = orthographic_rays(1024, r, u, f, margin=1.0)
    # Fraction of pixels inside the disk should approach pi/4.
    assert abs(mask.mean() - np.pi / 4) < 5e-3


def test_sphere_to_uv_roundtrip_known_points():
    pts = np.array([
        [1, 0, 0],    # lon=0, lat=0
        [0, 1, 0],    # lon=+90, lat=0
        [-1, 0, 0],   # lon=+/-180, lat=0
        [0, 0, 1],    # north pole
        [0, 0, -1],   # south pole
    ], dtype=np.float64)
    u, v = sphere_to_uv(pts, lon0=-np.pi)
    # u = (lon + pi) / 2pi
    np.testing.assert_allclose(u[0], 0.5, atol=1e-12)
    np.testing.assert_allclose(u[1], 0.75, atol=1e-12)
    assert u[2] in (0.0, 1.0) or np.isclose(u[2] % 1.0, 0.0, atol=1e-12)
    np.testing.assert_allclose(v[3], 0.0, atol=1e-12)
    np.testing.assert_allclose(v[4], 1.0, atol=1e-12)


def test_render_returns_correct_shape_and_dtype():
    tex = np.zeros((100, 200, 3), dtype=np.uint8)
    tex[..., 0] = 200
    out = render_disk(tex, size=64)
    assert out.shape == (64, 64, 3)
    assert out.dtype == np.uint8


def test_render_background_outside_disk():
    tex = np.full((100, 200, 3), 200, dtype=np.uint8)
    out = render_disk(
        tex, size=64, margin=1.5, background=(10, 20, 30),
    )
    # Corner pixel is definitely outside the disk.
    np.testing.assert_array_equal(out[0, 0], [10, 20, 30])


def test_render_picks_correct_hemisphere():
    """A texture split red(east)/blue(west): viewing from +X should show red."""
    h, w = 200, 400
    tex = np.zeros((h, w, 3), dtype=np.uint8)
    # lon0 = -pi: column index w/2 corresponds to lon = 0. Columns to the
    # right are positive longitude (= +Y hemisphere = "east").
    tex[:, w // 2:] = [255, 0, 0]   # east -> red
    tex[:, : w // 2] = [0, 0, 255]  # west -> blue

    # Camera on the +Y side looking toward -Y sees the east (red) hemisphere.
    out = render_disk(tex, view_direction=(0, -1, 0), size=128)
    center = out[64, 64]
    assert center[0] > 200 and center[2] < 50


def test_terminator_segments_lie_on_zero_cos_locus():
    """Every projected terminator point must un-project to a 3D point
    whose dot product with the sun unit vector is zero."""
    view = np.array([-1.0, 0.0, 0.0])
    sun = np.array([1.0, 1.0, 0.3])
    sun_unit = sun / np.linalg.norm(sun)
    r, u, f = camera_basis(view)

    xs, ys = terminator_segments(view_direction=view, sun_direction=sun)
    assert len(xs) >= 1 and len(xs) == len(ys)

    for u_im, v_im in zip(xs, ys):
        # On the near hemisphere: z (along forward) ≤ 0, so depth into the
        # disk is sqrt(1 - u^2 - v^2) taken with negative forward.
        z = np.sqrt(np.clip(1.0 - u_im**2 - v_im**2, 0.0, 1.0))
        pts = (u_im[:, None] * r + v_im[:, None] * u - z[:, None] * f)
        dots = pts @ sun_unit
        assert np.max(np.abs(dots)) < 1e-6


def test_terminator_disappears_for_full_disk_or_full_shadow():
    # Sun behind camera → entire visible hemisphere lit → no terminator
    # crosses the disk; the curve sits exactly on the limb so projects
    # to the unit circle (not "no segments", but |u^2+v^2| ≈ 1 everywhere).
    xs, ys = terminator_segments(view_direction=(-1, 0, 0),
                                 sun_direction=(1, 0, 0))
    for x, y in zip(xs, ys):
        r2 = x**2 + y**2
        assert np.all(r2 > 0.999)


def test_flatmap_no_rotation_no_sun_passes_texture_through():
    """With zero rotation and no sun, the flat map equals the texture
    up to one LSB of uint8 rounding (bilinear weight ≈ 0.999… on some
    pixels from the float64 round-trip)."""
    rng = np.random.default_rng(0)
    tex = rng.integers(0, 256, (90, 180, 3), dtype=np.uint8)
    out = render_flatmap(tex, return_array=True)
    assert out.shape == tex.shape
    diff = np.abs(out.astype(int) - tex.astype(int))
    assert diff.max() <= 1


def test_flatmap_rotation_shifts_pixels():
    """A 180° rotation moves the bright hemisphere from east to west."""
    h, w = 60, 120
    tex = np.zeros((h, w, 3), dtype=np.uint8)
    tex[:, w // 2:] = 200            # east hemisphere bright
    out = render_flatmap(tex, rotation_lon_deg=180, return_array=True)
    # After rotation, the left half of the output should be bright.
    assert out[h // 2, 5, 0] > 150
    assert out[h // 2, -5, 0] < 50


def test_flatmap_shading_brightens_sub_solar():
    """Sun at +X: output pixel at lon=0 (column center) is fully lit,
    pixel at lon=±180 (column edges) is at the ambient floor."""
    h, w = 90, 180
    tex = np.full((h, w, 3), 200, dtype=np.uint8)
    out = render_flatmap(tex, sun_direction=(1, 0, 0),
                         ambient=0.0, return_array=True)
    assert out[h // 2, w // 2, 0] > 195
    assert out[h // 2, 0, 0] < 5
    assert out[h // 2, -1, 0] < 5


def test_flatmap_terminator_lies_on_zero_cos_locus():
    sun = np.array([1.0, 1.0, 0.3])
    sun_unit = sun / np.linalg.norm(sun)
    xs, ys = flatmap_terminator(sun_direction=sun)
    assert len(xs) >= 1 and len(xs) == len(ys)
    for lon_deg, lat_deg in zip(xs, ys):
        lon = np.radians(lon_deg)
        lat = np.radians(lat_deg)
        P = np.stack([np.cos(lat) * np.cos(lon),
                      np.cos(lat) * np.sin(lon),
                      np.sin(lat)], axis=-1)
        dots = P @ sun_unit
        assert np.max(np.abs(dots)) < 1e-9


def test_sun_shading_darkens_terminator():
    tex = np.full((100, 200, 3), 200, dtype=np.uint8)
    # View from +X, sun also from +X -> whole visible disk fully lit.
    lit = render_disk(
        tex, view_direction=(-1, 0, 0), sun_direction=(1, 0, 0),
        ambient=0.0, size=128,
    )
    # View from +X, sun from -X -> visible disk in shadow (ambient only).
    dark = render_disk(
        tex, view_direction=(-1, 0, 0), sun_direction=(-1, 0, 0),
        ambient=0.0, size=128,
    )
    assert lit[64, 64, 0] > 150
    assert dark[64, 64, 0] < 10


def test_render_accepts_image_path(tmp_path):
    """render_disk / render_flatmap take a file path directly and open
    it via Pillow (decoder from the conventional file type)."""
    from pathlib import Path
    from PIL import Image

    rng = np.random.default_rng(1)
    tex = rng.integers(0, 256, (90, 180, 3), dtype=np.uint8)
    p = tmp_path / "tex.png"
    Image.fromarray(tex).save(p)

    # str and Path both work, and match passing the array directly.
    ref = render_disk(tex, view_direction=(-1, 0, 0), size=64)
    by_str = render_disk(str(p), view_direction=(-1, 0, 0), size=64)
    by_path = render_disk(Path(p), view_direction=(-1, 0, 0), size=64)
    np.testing.assert_array_equal(ref, by_str)
    np.testing.assert_array_equal(ref, by_path)

    flat = render_flatmap(str(p), return_array=True)
    assert flat.shape == tex.shape


def test_render_coerces_palette_image(tmp_path):
    """A palette ('P') PNG is decoded to real RGB, not raw indices."""
    from PIL import Image

    tex = np.zeros((90, 180, 3), dtype=np.uint8)
    tex[:, 90:] = (200, 30, 30)
    p = tmp_path / "pal.png"
    Image.fromarray(tex).convert("P").save(p)

    img = render_disk(p, view_direction=(-1, 0, 0),
                            up=(0, 1, 0), size=64)
    assert img.ndim == 3 and img.shape[-1] == 3   # RGB, not index plane
    assert int(img.max()) > 100                   # real colour values
