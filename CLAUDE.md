# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Install / common commands

```bash
pip install -e .[test]                  # core (numpy+Pillow+spiceypy+matplotlib) + pytest
pytest tests/                            # full suite (~1 s, 33 tests)
pytest tests/test_render.py::test_camera_basis_orthonormal   # single test
implanet-fetch                           # bulk-download auto-fetchable maps (~250 MB); --list/--body/--where
python scripts/fetch_maps.py             # dev shim, identical CLI (impl now lives in implanet/fetch.py)
python scripts/sync_registry.py          # mirror maps/*.json into implanet/assets/data/ after editing a registry
python scripts/build_attribution.py      # regenerate ATTRIBUTION.md from the registries
implanet <texture> <output> [--view x,y,z | --latlon lat,lon,0] [--sun x,y,z]   # CLI wrapper around render_disk
```

`tests/test_ephemeris.py` auto-skips if `spiceypy` or the SPICE kernels are missing. The first call to `ensure_kernels()` downloads ~32 MB of NAIF kernels (see asset layer below).

## Architecture: a 5-layer pipeline, body-fixed throughout

Everything in this package lives in the **body-fixed IAU rotation frame** of the rendered planet (+Z = north pole, +X = prime meridian on equator, +Y = 90° E). The two vector arguments that confuse most callers:

- `view_direction` points **camera → planet center** (not the other way).
- `sun_direction` points **planet → Sun**.

The codebase stacks four layers, each callable on its own; higher layers only depend on lower ones.

1. **`projection.py`** — pure geometry. `camera_basis()` builds an orthonormal (right, up, forward) triplet by re-orthogonalizing the `up` hint against `forward`. `orthographic_rays()` returns `(H, W, 3)` points on the near hemisphere of the unit sphere plus a disk mask; off-disk pixels are NaN. `sphere_to_uv()` converts sphere points to equirectangular texture coordinates with `lon0` controlling the longitude of the texture's left edge.
2. **`render.py`** — `render_disk()` glues those primitives to a bilinear texture sampler. Both `render_*` accept the `texture` as an ndarray, PIL.Image, **or a str/Path** (opened via Pillow by conventional file type; non-`L`/`RGB`/`RGBA` modes coerced to RGB) — handled centrally in `_as_texture_array`. The sampler **wraps in u** (so meridian seams stay continuous) and **clamps in v** (so poles don't read garbage). Optional Lambertian shading uses `shade = ambient + (1 - ambient) * max(0, P · sun_unit)`. The entire H×W work is vectorized — no per-pixel Python. **Returns just the rendered image** — a uint8 ndarray, row 0 = top. The disk occupies `[-1, +1]` planet radii on both axes; callers plotting with matplotlib use `extent=(-margin, +margin, -margin, +margin)`. `render_flatmap()` is the equirectangular-output counterpart that re-shades a texture in place without orthographic projection (returns a PIL.Image, or an array via `return_array=True`). `render_info()` mirrors the disk signature and returns a structured dict + a one-line caption for figure attributions.
3. **`overlays.py`** — vector overlays in unit-disk coordinates (u² + v² ≤ 1, visible hemisphere only): `graticule_segments`, `limb_circle`, `subobserver_point`, `terminator_segments` (the great circle `{P : P · sun_unit = 0}`, clipped at the limb), and `flatmap_terminator` (the lat/lon-space counterpart). Each returns plain `(xs, ys)` arrays so callers compose their own matplotlib plots from `render_disk` + overlays — there is no built-in publication-figure wrapper anymore.
4. **`ephemeris.py`** — thin SPICE wrappers. `sun_direction(body, utc)` and `sub_solar_point(body, utc)` go through J2000 + `pxform` rather than asking SPICE to resolve `IAU_<body>` directly — our `de440s.bsp` only carries planet barycenters, so moon SPK centers are unavailable; for moons, we use the parent barycenter as the position origin (sub-arcsecond error vs. AU baselines). Body table is in `_BODY_INFO`. `__init__.py` imports this module behind a `try/except ImportError`, so the package keeps working without `spiceypy`.

## Texture / map conventions

- Equirectangular textures are **2:1**, width = 2π longitude, height = π latitude, row 0 = north pole.
- `lon0=-π` (default) means texture column 0 sits at lon = −180°; pass `lon0=0` for textures whose column 0 is the prime meridian.

## Asset layer (`implanet.assets`) — registries + lazy cache

Nothing large is bundled in the wheel; textures and SPICE kernels download on first use. Two registries, two asset families:

- **`maps/manifest.json`** — texture maps (39 entries, ~22 bodies). Each entry has `asset_url` (auto) and/or `portal_url` (manual).
- **`maps/kernels.json`** — SPICE kernels. Each entry has a stable `id`, `url`, `size_bytes`, and `subdir` (cache placement). Categories: `generic` (lsk/pck/de440s), `spacecraft` (mission SPKs), `satellite` (jup365/nep105).

`implanet/assets/` is the single code path: `get_texture(body, variant=None)` and `get_kernel(id_or_filename)` return a local `Path`, downloading into the cache if absent. **When adding a map or kernel, edit the registry JSON — never hardcode URLs in code.** `ephemeris.py`, `examples/_flyby.py`, and `scripts/fetch_maps.py` all route through this layer.

Cache-dir resolution (first match wins): `$IMPLANET_KERNELS`/`$IMPLANET_MAPS` (explicit) → `$IMPLANET_CACHE/{kernels,maps}` → in-repo `kernels/` & `maps/data/` (dev checkout) → **`site-packages/implanet/_data/{kernels,maps}` (pip default — assets live *with* the package)** → `~/.cache/implanet/...` (only if `_data` is read-only). The package-dir default is a deliberate user choice; `implanet/_data/` is gitignored and never shipped in the wheel (45 KB, JSON registries only). `implanet.fetch` is the packaged bulk-downloader behind the `implanet-fetch` entry point.

The registries are duplicated into `implanet/assets/data/` so wheels ship them (the loader prefers the repo `maps/*.json`, falls back to the packaged copy). **After editing either registry, run `python scripts/sync_registry.py`** — `tests/test_assets.py` fails if the repo and packaged copies drift.

## Things to watch out for

- The `view_direction` / `sun_direction` direction conventions are easy to flip — `view_direction_from_earth()` deliberately returns the body→Earth vector and the docstring tells the caller to **negate it** before feeding to `render_disk`.
- The Sun is intentionally missing from `_BODY_INFO`: rendering the Sun calls for `ambient=1.0` (flat shading), not a sun-direction lookup. Same applies to SAR mosaics like Venus where pixel values already encode reflectance.
- `Layer 1` (`projection.py`) and `Layer 2` (`render.py`) only depend on numpy + Pillow. Don't introduce matplotlib or spiceypy imports below `ephemeris.py` — the optional-dependency boundary is load-bearing.
- Examples generate large output trees under `examples/figures*/` and `examples/animations/`; these are gitignored regeneratable artifacts, not source.
