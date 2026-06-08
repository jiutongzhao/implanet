"""Smoke + geometric correctness tests for implanet."""

import numpy as np
import pytest

from implanet import (
    render_disk, render_flatmap, render_info,
    camera_basis, sphere_to_uv,
    disk_terminator, flatmap_terminator,
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
    # Default background=None → RGBA output (alpha=0 outside the disk).
    out = render_disk(tex, size=64)
    assert out.shape == (64, 64, 4)
    assert out.dtype == np.uint8
    assert out[0, 0, 3] == 0           # transparent corner
    assert out[32, 32, 3] == 255       # opaque centre

    # Opting back into an opaque fill returns plain RGB.
    rgb = render_disk(tex, size=64, background="white")
    assert rgb.shape == (64, 64, 3)


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


def test_disk_terminator_lie_on_zero_cos_locus():
    """Every projected terminator point must un-project to a 3D point
    whose dot product with the sun unit vector is zero."""
    view = np.array([-1.0, 0.0, 0.0])
    sun = np.array([1.0, 1.0, 0.3])
    sun_unit = sun / np.linalg.norm(sun)
    r, u, f = camera_basis(view)

    xs, ys = disk_terminator(view_direction=view, sun_direction=sun)
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
    xs, ys = disk_terminator(view_direction=(-1, 0, 0),
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


def test_rgba_shading_preserves_alpha():
    """Shading must darken RGB but leave the alpha channel intact — a
    night-side RGBA pixel stays fully opaque on the disk (alpha 255),
    only its colour goes dark."""
    tex = np.dstack([np.full((100, 200), 200, np.uint8)] * 3
                    + [np.full((100, 200), 255, np.uint8)])  # opaque RGBA
    # View +X, sun -X → centre pixel is on the night side.
    dark = render_disk(tex, view_direction=(-1, 0, 0),
                       sun_direction=(-1, 0, 0), ambient=0.0, size=128)
    assert dark.shape[-1] == 4
    assert dark[64, 64, 3] == 255          # disk stays opaque
    assert dark[64, 64, 0] < 10            # but the colour is shaded dark
    # off-disk corner is transparent
    assert dark[0, 0, 3] == 0


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


def test_render_info_returns_structured_dict():
    """render_info echoes inputs and derives sub-observer/sub-solar
    latitudes — independently of any registry lookup."""
    info = render_info(
        np.zeros((100, 200, 3), dtype=np.uint8),
        view_direction=(-1, 0, 0),
        sun_direction=(1, 0, 0),
    )
    # top-level shape
    for k in ("texture", "camera", "sun", "output", "caption"):
        assert k in info

    # raw ndarray has no manifest record → texture fields stay None
    assert info["texture"]["body"] is None
    assert info["texture"]["citation"] is None

    # camera: view_direction (-1, 0, 0) → sub-observer at (lat=0, lon=0)
    assert info["camera"]["view_direction"] == (-1.0, 0.0, 0.0)
    assert abs(info["camera"]["sub_observer_lat_deg"]) < 1e-9
    assert abs(info["camera"]["sub_observer_lon_deg"]) < 1e-9

    # sun (1, 0, 0) → sub-solar at (0, 0); 0.3 in z would tilt north
    assert info["sun"] is not None
    assert abs(info["sun"]["sub_solar_lat_deg"]) < 1e-9
    assert "sub-obs" in info["caption"]
    assert "sun" in info["caption"]


def test_render_info_finds_texture_via_manifest():
    """When passed a registered filename, render_info pulls citation /
    license / mission from the manifest."""
    from implanet.assets._registry import texture_entries
    e = next(x for x in texture_entries() if x["body"] == "Mars")
    info = render_info(e["filename"], view_direction=(-1, 0, 0))
    assert info["texture"]["body"] == "Mars"
    assert info["texture"]["citation"]
    assert info["texture"]["license"]
    assert info["caption"].startswith("Mars")


def test_render_background_accepts_matplotlib_color_string():
    """background= takes any matplotlib color spec, not just RGB tuples."""
    tex = np.full((50, 100, 3), 200, dtype=np.uint8)
    out_named = render_disk(tex, size=64, margin=1.5, background="white")
    out_hex   = render_disk(tex, size=64, margin=1.5, background="#ffffff")
    out_grey  = render_disk(tex, size=64, margin=1.5, background="0.25")
    out_tuple = render_disk(tex, size=64, margin=1.5, background=(255, 255, 255))

    # Corner is outside the disk → it carries the background colour.
    np.testing.assert_array_equal(out_named[0, 0], [255, 255, 255])
    np.testing.assert_array_equal(out_hex[0, 0],   [255, 255, 255])
    np.testing.assert_array_equal(out_named[0, 0], out_tuple[0, 0])

    # "0.25" = 25% grey ≈ 64
    g = int(out_grey[0, 0, 0])
    assert 60 <= g <= 68


def test_render_info_no_sun_omits_sun_block():
    info = render_info(np.zeros((90, 180, 3), dtype=np.uint8),
                       view_direction=(-1, 0, 0))
    assert info["sun"] is None
    assert "sun" not in info["caption"].lower()


def test_resolve_view_presets():
    """Each preset gives an orthonormal camera and sits the camera on
    the named (signed) axis: the sub-observer point is exactly -forward
    and lands on the named axis."""
    from implanet import resolve_view

    cases = {
        "x":   (1, 0, 0),       # camera on +X → sub-obs at +X
        "-x":  (-1, 0, 0),
        "y":   (0, 1, 0),
        "-y":  (0, -1, 0),
        "z":   (0, 0, 1),       # north pole
        "-z":  (0, 0, -1),
        "yz":  (1, 0, 0),       # ≡ +X (prime meridian equator view)
        "xy":  (0, 0, 1),       # ≡ +Z
        "xz":  (0, 1, 0),       # ≡ +Y
    }
    for name, expected_sub_obs in cases.items():
        view, up = resolve_view(name)
        r, u, f = camera_basis(view, up)
        # camera_basis must succeed → preset's up is never parallel to view
        sub_obs = -f
        np.testing.assert_allclose(sub_obs, expected_sub_obs, atol=1e-12)


def test_resolve_view_accepts_case_and_plus_prefix():
    from implanet import resolve_view

    for name in ("YZ", "yz", "+YZ", "+yz", "  yz  "):
        view, up = resolve_view(name)
        assert tuple(view) == (-1.0, 0.0, 0.0)
        assert tuple(up) == (0.0, 0.0, 1.0)


def test_resolve_view_unknown_preset_raises():
    from implanet import resolve_view
    with pytest.raises(ValueError):
        resolve_view("not_a_preset")


def test_resolve_view_explicit_up_wins():
    from implanet import resolve_view
    view, up = resolve_view("yz", up=(0, 1, 0))
    assert tuple(up) == (0, 1, 0)


def test_render_disk_accepts_preset_view_string():
    """``view_direction="yz"`` reproduces the explicit prime-meridian view."""
    tex = np.zeros((90, 180, 3), dtype=np.uint8)
    tex[:, 90:] = (200, 30, 30)         # east bright red
    a = render_disk(tex, view_direction=(-1, 0, 0), size=96)
    b = render_disk(tex, view_direction="yz", size=96)
    np.testing.assert_array_equal(a, b)


def test_render_disk_polar_preset_picks_inplane_up():
    """The "z" preset uses an in-plane up — no degeneracy error."""
    tex = np.full((60, 120, 3), 200, dtype=np.uint8)
    out = render_disk(tex, view_direction="z", size=64)   # north pole
    assert out.shape == (64, 64, 4)   # RGBA from the transparent default
    # disk centre is on the sphere → fully sampled
    assert int(out[32, 32, 0]) > 150


def test_render_disk_accepts_body_name_string(tmp_path, monkeypatch):
    """A bare body name routes through the texture registry."""
    from PIL import Image as PILImage
    calls = []
    fake_path = tmp_path / "fake_mars.png"
    PILImage.fromarray(
        np.full((60, 120, 3), 123, dtype=np.uint8)
    ).save(fake_path)

    def fake_get_texture(body, variant=None, **kw):
        calls.append((body, variant))
        return fake_path

    # Patch the module the renderer actually imports from.
    import implanet.assets as assets_mod
    monkeypatch.setattr(assets_mod, "get_texture", fake_get_texture)

    out = render_disk("Mars", view_direction="yz", size=64)
    assert calls == [("Mars", None)]
    # All sampled pixels should be the synthetic constant.
    assert int(out[32, 32, 0]) > 100


def test_render_info_resolves_body_name():
    """render_info("Mars") looks up the registry without opening the file."""
    info = render_info("Mars", view_direction="yz")
    assert info["texture"]["body"] == "Mars"
    assert info["texture"]["citation"]


def test_plot_disk_returns_axes_with_image():
    """plot_disk composes render_disk + overlays into a matplotlib axes."""
    import matplotlib
    matplotlib.use("Agg")
    from implanet import plot_disk

    tex = np.full((60, 120, 3), 180, dtype=np.uint8)
    fig, ax = plot_disk(tex, view_direction="yz", sun_direction=(1, 0, 0),
                        size=128)
    # imshow + overlays = at least one image + several Line2D children
    assert any(im for im in ax.images)
    assert len(ax.lines) >= 2     # limb + at least one graticule/terminator/marker

    import matplotlib.pyplot as plt
    plt.close(fig)


def test_plot_disk_preserves_caller_axes_styling():
    """When `ax` is provided, plot_disk leaves the caller's ticks /
    labels / limits / aspect / spines alone — only the disk image and
    the overlay polylines are added."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from implanet import plot_disk

    fig, ax = plt.subplots()
    ax.set_xlim(-3.0, 3.0)
    ax.set_ylim(-2.0, 2.0)
    ax.set_aspect("auto")
    ax.set_xticks([-2.0, 0.0, 2.0])
    ax.set_xlabel("custom x")
    ax.set_ylabel("custom y")
    spine_states = {k: v.get_visible() for k, v in ax.spines.items()}

    tex = np.full((60, 120, 3), 180, dtype=np.uint8)
    plot_disk(tex, view_direction="yz", sun_direction=(1, 0, 0),
              size=64, ax=ax)

    assert ax.get_xlim() == (-3.0, 3.0)
    assert ax.get_ylim() == (-2.0, 2.0)
    assert ax.get_aspect() == "auto"
    assert list(ax.get_xticks()) == [-2.0, 0.0, 2.0]
    assert ax.get_xlabel() == "custom x"
    assert ax.get_ylabel() == "custom y"
    for k, v in spine_states.items():
        assert ax.spines[k].get_visible() == v
    # but the disk + overlays did get drawn
    assert ax.images
    assert ax.lines
    plt.close(fig)


def test_plot_disk_style_axes_force_true_on_passed_axes():
    """`style_axes=True` re-applies the disk styling even on a caller-
    provided axes — for users who want the clean plate look in a
    sub-axes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from implanet import plot_disk

    fig, ax = plt.subplots()
    ax.set_xlim(-3.0, 3.0)
    tex = np.full((60, 120, 3), 180, dtype=np.uint8)
    plot_disk(tex, view_direction="yz", size=64, ax=ax, style_axes=True,
              margin=1.05)
    assert ax.get_xlim() == (-1.05, 1.05)
    plt.close(fig)


def test_plot_disk_preset_auto_sun_is_fixed_plus_x():
    """Auto-sun for every preset is the body-fixed +X direction. Each
    preset just sees the same lit prime meridian from its own angle:
    ``"yz"`` is fully lit (sub-solar = sub-observer), ``"y"`` sees a
    terminator across the middle, ``"-yz"`` is in shadow."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from implanet import plot_disk

    tex = np.full((60, 120, 3), 200, dtype=np.uint8)

    # "y" preset: camera on +Y, sun on +X → terminator down the centre.
    # Sample inside a 60-px radius (the disk itself ≈ 61 px at this size).
    disk = np.linalg.norm(np.indices((128, 128)) - 63.5, axis=0) < 60
    fig, ax = plot_disk(tex, view_direction="y", size=128, ambient=0.0,
                        show_subobserver=False, show_graticule=False,
                        show_limb=False, show_terminator=False)
    img = ax.images[0].get_array()
    interior = img[disk]
    assert interior.min() < 30           # night side fades to ambient=0
    assert interior.max() > 150          # day side is well lit
    assert interior.max() - interior.min() > 120  # clear terminator gradient
    plt.close(fig)

    # "yz" preset: camera on +X, sun also on +X → disk centre fully lit.
    # P_x = sqrt(1 - r²) so brightness falls off toward the limb even
    # though the visible hemisphere is entirely day-side; sample only
    # the bright inner cap (r_pix < 30 of a ~61 px disk ⇒ P_x > 0.87).
    bright_disk = np.linalg.norm(np.indices((128, 128)) - 63.5, axis=0) < 30
    fig, ax = plot_disk(tex, view_direction="yz", size=128, ambient=0.0,
                        show_subobserver=False, show_graticule=False,
                        show_limb=False, show_terminator=False)
    img = ax.images[0].get_array()
    interior = img[bright_disk]
    assert interior.min() > 150     # uniformly bright (limb attenuates)
    plt.close(fig)

    # "-yz" preset: camera on -X, sun on +X → visible disk in shadow.
    fig, ax = plot_disk(tex, view_direction="-yz", size=128, ambient=0.0,
                        show_subobserver=False, show_graticule=False,
                        show_limb=False, show_terminator=False)
    img = ax.images[0].get_array()
    # Default RGBA output: alpha=255 inside the disk; slice it off and
    # check the colour channels are dark.
    interior = img[bright_disk][..., :3]
    assert interior.max() < 30      # fully dark
    plt.close(fig)

    # sun_direction="off" overrides → flat albedo no matter the preset.
    fig, ax = plot_disk(tex, view_direction="y", size=128,
                        sun_direction="off", ambient=0.0,
                        show_subobserver=False, show_graticule=False,
                        show_limb=False, show_terminator=False)
    img = ax.images[0].get_array()
    interior = img[bright_disk]
    assert interior.min() > 190
    plt.close(fig)


def test_plot_disk_explicit_view_vector_does_not_inject_sun():
    """When `view_direction` is a 3-vector the auto-sun is *not*
    triggered — preserves the prior None == no-shading contract for
    callers who used to rely on it."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from implanet import plot_disk

    tex = np.full((60, 120, 3), 200, dtype=np.uint8)
    fig, ax = plot_disk(tex, view_direction=(-1, 0, 0), size=128,
                        ambient=0.0, show_subobserver=False,
                        show_graticule=False, show_limb=False,
                        show_terminator=False)
    img = ax.images[0].get_array()
    # No shading applied → whole disk is at the texture's flat 200.
    disk = np.linalg.norm(np.indices(img.shape[:2]) - 64, axis=0) < 50
    assert img[disk].min() > 190
    plt.close(fig)


def test_plot_disk_polar_preset_no_degeneracy():
    """North-pole preset must not crash on the camera basis."""
    import matplotlib
    matplotlib.use("Agg")
    from implanet import plot_disk

    tex = np.full((60, 120, 3), 180, dtype=np.uint8)
    fig, ax = plot_disk(tex, view_direction="xy", size=128,
                        show_subobserver=False)
    assert ax.images
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_render_coerces_palette_image(tmp_path):
    """A palette ('P') PNG is decoded to real RGB, not raw indices."""
    from PIL import Image

    tex = np.zeros((90, 180, 3), dtype=np.uint8)
    tex[:, 90:] = (200, 30, 30)
    p = tmp_path / "pal.png"
    Image.fromarray(tex).convert("P").save(p)

    img = render_disk(p, view_direction=(-1, 0, 0),
                            up=(0, 1, 0), size=64)
    # 4 here = RGBA from the transparent default; 3 if a caller opts
    # into an opaque background. Either way, not the 1-channel palette.
    assert img.ndim == 3 and img.shape[-1] in (3, 4)
    assert int(img.max()) > 100                   # real colour values
