"""Smoke + geometric correctness tests for implanet."""

import numpy as np
import pytest

from implanet import render_planet, camera_basis, sphere_to_uv, terminator_segments
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
    out = render_planet(tex, size=64, return_array=True)
    assert out.shape == (64, 64, 3)
    assert out.dtype == np.uint8


def test_render_background_outside_disk():
    tex = np.full((100, 200, 3), 200, dtype=np.uint8)
    out = render_planet(
        tex, size=64, margin=1.5, background=(10, 20, 30), return_array=True
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
    out = render_planet(tex, view_direction=(0, -1, 0), size=128, return_array=True)
    center = out[64, 64]
    assert center[0] > 200 and center[2] < 50


def test_terminator_segments_lie_on_zero_cos_locus():
    """Every projected terminator point must un-project to a 3D point
    whose dot product with the sun unit vector is zero."""
    view = np.array([-1.0, 0.0, 0.0])
    sun = np.array([1.0, 1.0, 0.3])
    sun_unit = sun / np.linalg.norm(sun)
    r, u, f = camera_basis(view)

    segs = terminator_segments(view_direction=view, sun_direction=sun)
    assert len(segs) >= 1

    for seg in segs:
        u_im, v_im = seg[:, 0], seg[:, 1]
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
    segs = terminator_segments(view_direction=(-1, 0, 0),
                               sun_direction=(1, 0, 0))
    for seg in segs:
        r2 = seg[:, 0]**2 + seg[:, 1]**2
        assert np.all(r2 > 0.999)


def test_sun_shading_darkens_terminator():
    tex = np.full((100, 200, 3), 200, dtype=np.uint8)
    # View from +X, sun also from +X -> whole visible disk fully lit.
    lit = render_planet(
        tex, view_direction=(-1, 0, 0), sun_direction=(1, 0, 0),
        ambient=0.0, size=128, return_array=True,
    )
    # View from +X, sun from -X -> visible disk in shadow (ambient only).
    dark = render_planet(
        tex, view_direction=(-1, 0, 0), sun_direction=(-1, 0, 0),
        ambient=0.0, size=128, return_array=True,
    )
    assert lit[64, 64, 0] > 150
    assert dark[64, 64, 0] < 10
