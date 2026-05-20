"""Tests for the implanet.assets registry + cache layer."""

import filecmp
import json
from pathlib import Path

import pytest

from implanet import assets
from implanet.assets import _cache, _registry

REPO = Path(__file__).resolve().parent.parent


def test_packaged_registries_match_repo_sources():
    """The wheel-shipped copies must stay byte-identical to maps/*.json
    (run scripts/sync_registry.py after editing either)."""
    for name in ("manifest.json", "kernels.json"):
        src = REPO / "maps" / name
        pkg = REPO / "implanet" / "assets" / "data" / name
        assert pkg.is_file(), f"missing packaged copy {pkg}"
        assert filecmp.cmp(src, pkg, shallow=False), (
            f"{name} drift: run `python scripts/sync_registry.py`"
        )


def test_kernel_registry_schema():
    for e in _registry.kernel_entries():
        for field in ("id", "filename", "category", "subdir", "url",
                      "size_bytes", "license"):
            assert field in e, f"kernel {e.get('id')} missing {field}"
        assert e["category"] in ("generic", "spacecraft", "satellite")
        assert e["url"].startswith("https://")


def test_kernel_ids_unique():
    ids = [e["id"] for e in _registry.kernel_entries()]
    assert len(ids) == len(set(ids))


def test_generic_kernel_ids_present():
    from implanet import ephemeris
    known = {e["id"] for e in _registry.kernel_entries()}
    for kid in ephemeris._GENERIC_KERNEL_IDS:
        assert kid in known


def test_find_kernel_by_id_and_filename():
    by_id = _registry.find_kernel("de440s")
    by_file = _registry.find_kernel("de440s.bsp")
    assert by_id is by_file
    with pytest.raises(KeyError):
        _registry.find_kernel("does_not_exist")


def test_find_texture_default_prefers_downloadable():
    e = _registry.find_texture("Mars")
    assert e["body"] == "Mars"
    assert e.get("asset_url")
    with pytest.raises(KeyError):
        _registry.find_texture("Mars", variant="no_such_variant")


def test_cache_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("IMPLANET_CACHE", str(tmp_path))
    monkeypatch.delenv("IMPLANET_KERNELS", raising=False)
    monkeypatch.delenv("IMPLANET_MAPS", raising=False)
    assert _cache.cache_base() == tmp_path
    assert _cache.kernels_dir() == tmp_path / "kernels"
    assert _cache.maps_dir() == tmp_path / "maps"


def test_kernels_env_takes_priority(monkeypatch, tmp_path):
    monkeypatch.setenv("IMPLANET_KERNELS", str(tmp_path / "k"))
    assert _cache.kernels_dir() == tmp_path / "k"


def test_package_base_lives_inside_the_installed_package():
    """The pip default keeps assets *with the package*:
    <implanet>/_data, a sibling of this _cache module's package dir."""
    import implanet
    pkg_root = Path(implanet.__file__).resolve().parent
    assert _cache._package_base() == pkg_root / "_data"


def test_default_base_falls_back_when_package_dir_readonly(
    monkeypatch, tmp_path
):
    """If site-packages is read-only, _default_base() must not raise —
    it falls back to the user cache so downloads still work."""
    _cache._default_base.cache_clear()
    ro = tmp_path / "ro_pkg" / "_data"
    monkeypatch.setattr(_cache, "_package_base", lambda: ro)

    def boom(*a, **k):
        raise PermissionError("read-only install")

    monkeypatch.setattr(Path, "mkdir", boom)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "uc"))
    try:
        assert _cache._default_base() == tmp_path / "uc" / "implanet"
    finally:
        _cache._default_base.cache_clear()


def test_kernel_path_uses_subdir():
    p = assets.kernel_path("messenger_cruise")
    assert p.parent.name == "messenger"
    assert p.name == "msgr_040803_080216_120401.bsp"
    g = assets.kernel_path("de440s")          # generic → no subdir
    assert g.name == "de440s.bsp"
    assert g.parent.name != "data"


def test_get_kernel_missing_without_download(monkeypatch, tmp_path):
    monkeypatch.setenv("IMPLANET_CACHE", str(tmp_path))
    monkeypatch.delenv("IMPLANET_KERNELS", raising=False)
    with pytest.raises(FileNotFoundError):
        assets.get_kernel("de440s", download_if_missing=False)


def test_synthetic_daynight_texture(monkeypatch, tmp_path):
    """The generated reference texture: 2:1, three tone levels, and the
    day hemisphere (lon 0 / +X) renders white while night renders black."""
    import numpy as np
    from PIL import Image
    from implanet import render_disk

    monkeypatch.setenv("IMPLANET_CACHE", str(tmp_path))
    monkeypatch.delenv("IMPLANET_MAPS", raising=False)

    p = assets.get_texture("Reference", "daynight")
    assert p.exists() and p.parent == tmp_path / "maps"
    arr = np.asarray(Image.open(p))
    h, w, _ = arr.shape
    assert w == 2 * h                                  # equirectangular 2:1
    # White dayside and a GREY (not black) shaded side both present
    # under the overlaid graticule.
    assert {110, 245}.issubset(set(np.unique(arr[..., 0])))

    day = render_disk(Image.open(p).convert("RGB"),
                            view_direction=(-1, 0, 0), size=128)
    night = render_disk(Image.open(p).convert("RGB"),
                              view_direction=(1, 0, 0), size=128)
    # Grid-tolerant whole-disk means (default black off-disk pulls both
    # down equally). Day is clearly brighter; the shaded side is
    # mid-grey, well above near-black.
    assert day.mean() > night.mean() + 50
    assert day.mean() > 150
    assert 60 < night.mean() < 170


def test_attribution_returns_required_fields():
    """Per-entry attribution dict has all citation fields wired up
    (any single field may legitimately be empty in the registry; here
    we assert the *keys* exist and the umbrella note is non-empty)."""
    from implanet import attribution
    a = attribution("Mars")
    for field in ("body", "variant", "agency", "mission", "instrument",
                  "provenance", "license", "citation", "portal_url",
                  "asset_url", "note", "umbrella_license_notes"):
        assert field in a, f"attribution() missing field {field}"
    assert a["body"] == "Mars"
    assert a["umbrella_license_notes"]            # top-level note present
    assert a["license"]                            # the texture has a license
    assert a["citation"]                           # and a citation string


def test_attribution_for_specific_variant():
    from implanet import attribution
    a = attribution("Earth", "natural_earth3")
    assert a["variant"] == "natural_earth3"
    assert "Natural Earth" in a["citation"]


def test_show_attribution_prints_umbrella_and_entry(capsys):
    from implanet import show_attribution
    show_attribution("Mars")
    out = capsys.readouterr().out
    assert "UMBRELLA LICENSE NOTES" in out
    assert "Mars" in out
    assert "license" in out
    assert "citation" in out


def test_attribution_md_in_sync_with_registries(tmp_path, monkeypatch):
    """ATTRIBUTION.md at the repo root must stay in lockstep with the
    JSON registries — re-run `python scripts/build_attribution.py`
    after editing manifest/kernels."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "build_attribution", REPO / "scripts" / "build_attribution.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Redirect OUT to a temp path, regenerate, and diff against the
    # committed file.
    fresh = tmp_path / "ATTRIBUTION.md"
    monkeypatch.setattr(mod, "OUT", fresh)
    rc = mod.main()
    assert rc == 0

    committed = REPO / "ATTRIBUTION.md"
    assert committed.is_file(), "ATTRIBUTION.md missing — run scripts/build_attribution.py"
    assert fresh.read_text() == committed.read_text(), (
        "ATTRIBUTION.md drift — run `python scripts/build_attribution.py`"
    )


def test_manual_only_texture_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("IMPLANET_CACHE", str(tmp_path))
    monkeypatch.delenv("IMPLANET_MAPS", raising=False)
    # messenger_basemap_fullres is portal-only (no asset_url).
    with pytest.raises((ValueError, KeyError)):
        assets.get_texture("Mercury", "messenger_basemap_fullres")
