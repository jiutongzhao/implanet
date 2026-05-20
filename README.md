# implanet

Render a planet's equirectangular map into a 2D orthographic view from any
viewing direction, with optional SPICE-driven sun lighting and a
publication-style matplotlib figure layer.

```
                        +---------- matplotlib figure -----------+
                        |   white bg · dashed graticule · ticks  |
                        |                                        |
   equirectangular  →   |          rendered disk on axes         |
   texture (2:1)        |    [-1,+1] planet radii                |
                        |                                        |
                        |   sub-obs (lat, lon)  ·  sub-solar     |
                        +----------------------------------------+
                                       ↑
                          SPICE (spiceypy) → sun_direction
```

## Install

```bash
pip install implanet                # everything — one command, no extras
```

That single install pulls in numpy, Pillow, spiceypy *and* matplotlib,
so rendering, SPICE ephemerides, and the figure layer all work out of
the box. (Developing the package: `pip install -e .[test]` adds pytest.)

Python ≥ 3.9. Two console scripts are installed:

```bash
implanet <texture> <output> [...]   # render one disk to a file
implanet-fetch [--list|--body ...]  # bulk-download maps
```

**Assets are not bundled** — textures and SPICE kernels download on first
use. By default they live *with the package*
(`site-packages/implanet/_data/{maps,kernels}`); in a dev checkout the
repo's `maps/data/` and `kernels/` are reused instead. Override with
`IMPLANET_CACHE=/some/dir` (or `IMPLANET_MAPS` / `IMPLANET_KERNELS` for
fine control). The first `ensure_kernels()` pulls ~32 MB of generic NAIF
kernels; individual textures download as you request them.

## Quick start

```python
from PIL import Image
from implanet import render_disk, get_texture

# get_texture downloads (once) and returns a local path. render_disk
# accepts that path directly — no need to open it yourself.
img, x, y = render_disk(
    get_texture("Earth"),              # str/Path | PIL.Image | ndarray
    view_direction=(-1, -0.2, -0.3),   # camera → planet center, body-fixed
    sun_direction=(1, 0.5, 0.4),       # planet → Sun
    size=600,
)
Image.fromarray(img).save("earth.png")
# Or plot it yourself — x, y are pixel-edge coords in planet radii so the
# disk lands at [-1, +1] on both axes:
#   ax.imshow(img, extent=(x.min(), x.max(), y.min(), y.max()))
#   ax.set_aspect("equal")
```

`get_texture(body, variant=None)` picks the body's default map; pass a
variant for a specific one, e.g. `get_texture("Earth", "natural_earth3")`.

For a publication-style figure (white background, dashed lat/lon grid,
axis ticks in planet radii):

```python
from implanet import get_texture
from implanet.figure import plot_planet
fig, ax = plot_planet(get_texture("Earth"),
                      view_direction=(-1,-0.2,-0.3),
                      sun_direction=(1,0.5,0.4),
                      body_name="Earth",
                      source_text="NASA Visible Earth · Blue Marble")
fig.savefig("earth_scientific.png", dpi=140, bbox_inches="tight")
```

With real ephemerides:

```python
import math
from implanet import sun_direction, sub_solar_point, get_texture
from implanet.figure import plot_planet

utc = "2026-05-14T12:00:00"
sun = sun_direction("Mars", utc)
lat, lon = sub_solar_point("Mars", utc)
# camera 30° west of the sub-solar point → day side with a visible terminator
lon_cam = math.radians(lon - 30)
lat_cam = math.radians(lat)
view = (-math.cos(lat_cam)*math.cos(lon_cam),
        -math.cos(lat_cam)*math.sin(lon_cam),
        -math.sin(lat_cam))

fig, _ = plot_planet(get_texture("Mars"),
                     view_direction=view, sun_direction=sun,
                     title=f"Mars  {utc} UTC")
fig.savefig("mars.png")
```

## Conventions

All vectors live in the **body-fixed IAU frame** of the rendered body:

- **+Z** — rotation axis (north pole)
- **+X** — prime meridian at the equator
- **+Y** — 90° east longitude
- right-handed

Two vector inputs flip readers up most:

| Argument | Convention |
|---|---|
| `view_direction` | camera **→** planet center |
| `sun_direction` | planet **→** Sun |

The texture is **equirectangular** (2:1 aspect, lon spans 2π, lat spans π,
row 0 = north pole). `lon0` shifts the texture's left edge in radians:

- `lon0=-π` (default) — texture column 0 sits at lon = −180°
- `lon0=0` — texture column 0 sits at the prime meridian

## How rendering works

`render_disk` does orthographic projection of a textured unit sphere
and (optionally) Lambertian shading. All steps are fully vectorized in
NumPy — there are no per-pixel Python loops.

```
   equirectangular           camera basis           visible hemisphere
   texture  T(λ, φ)     ─→   (right, up,    ─→     of unit sphere
   (H, W, C)                  forward)              S² ∩ {P·forward ≤ 0}
                                                          │
                                                          ▼
                                                    image pixel (u, v)
                                                    ─→ 3D point P
                                                    ─→ (lat, lon)
                                                    ─→ bilinear sample T
                                                    ─→ optional shade × albedo
```

### 1.  Camera basis

From `view_direction` (camera → planet center) and the `up` hint we
build an orthonormal triplet (`right`, `up`, `forward`) by
re-orthogonalizing `up` against `forward`. The camera sits at
−∞·`forward` (orthographic limit). Code: `camera_basis()` in
`projection.py`.

### 2.  Pixel → 3D point on the visible hemisphere

Output image pixels (px, py) map to normalized image-plane coordinates

    u = (px − cx) / R           v = −(py − cy) / R

where R is the disk radius in pixels (`min(H, W) / 2 / margin`).
Pixels with u² + v² > 1 fall outside the disk and are filled with
`background`. For the rest, the point on the *near* hemisphere of the
unit sphere is

    z = √(1 − u² − v²)
    P = u·right + v·up − z·forward       (world coords, body-fixed)

The near hemisphere is the one with P·`forward` ≤ 0 — the side facing
the camera. Code: `orthographic_rays()`.

### 3.  Sphere → texture coordinates

For each surface point P = (Px, Py, Pz) on the unit sphere,

    lat = arcsin(Pz)                      ∈ [−π/2, π/2]
    lon = atan2(Py, Px)                   ∈ [−π,    π]

mapped to the texture's normalized coordinates

    u_tex = ((lon − lon0) / 2π)  mod 1
    v_tex = ½ − lat / π

The `mod 1` in u handles longitude wrap-around at the seam; v clamps at
the poles. `lon0` lets you shift textures whose column 0 sits at the
prime meridian instead of −180°. Code: `sphere_to_uv()`.

### 4.  Bilinear sampling with seam-correct wrap

The four neighboring texels around `(u_tex·W − ½, v_tex·H − ½)` are
fetched with **wrap-around in u** and **clamp in v**, then mixed with
fractional weights. Wrapping is what keeps a meridian line continuous
at the texture's left/right seam; clamping prevents bogus reads above
the north pole / below the south. Code: `_sample_bilinear()` in
`render.py`.

### 5.  Optional Lambertian shading

If `sun_direction` *s* (a unit vector, planet → Sun) is given, the
local surface normal on a unit sphere is just P itself, so the cosine
of the solar incidence angle is

    cos i = max(0,  P · s)

The pixel color is then multiplied by

    shade = ambient  +  (1 − ambient) · cos i

with `ambient ∈ [0, 1]` setting the floor on the night side. Setting
`ambient = 1.0` disables shading (used for the Sun and for SAR mosaics
like Venus, whose pixel values already encode reflectance).

### 6.  Compositing

Off-disk pixels are replaced with `background`, the array is clipped
to [0, 255] and cast to `uint8`. Grayscale, RGB, and RGBA all flow
through the same path; the output mode is inferred from the input
channel count.

### Cost

The work is dominated by the `H × W` bilinear gather, which is a
constant 4 lookups per pixel. A 720×720 render of an 8K texture takes
~50 ms on this machine; the full 15-figure scientific batch
(`examples/scientific_figures.py`) runs in under 25 s including SPICE
calls.

## API

### Layer 1 — Rendering

```python
image, x, y = render_disk(
    texture,                       # str/Path | PIL.Image | ndarray (H,W)|(H,W,C)
    view_direction=(1, 0, 0),
    up=(0, 0, 1),                  # world-up hint
    size=512,                      # int or (h, w)
    margin=1.05,                   # 1.0 = disk touches the shorter edge
    lon0=-math.pi,
    sun_direction=None,            # None → flat albedo (no shading)
    ambient=0.15,                  # [0, 1]; floor on Lambertian shading
    background=(0, 0, 0),          # RGB 0-255 for off-disk pixels
)
# image: uint8 ndarray (H, W) or (H, W, C)
# x:     length W+1 pixel-edge coords, increasing from -margin to +margin (planet radii)
# y:     length H+1 pixel-edge coords, decreasing from +margin to -margin (matches row 0 = top)
# → Save: Image.fromarray(image).save(...)
# → Plot: ax.pcolormesh(x, y, image); ax.set_aspect("equal")
```

### Layer 2 — Geometry primitives

Used internally by `render_disk`, exposed if you need to build your own
pipeline.

```python
camera_basis(view_direction, up=(0,0,1))           # → (right, up, forward)
orthographic_rays(size, right, up, forward, margin=1.0)
                                                   # → (HxWx3 points, HxW mask)
sphere_to_uv(points, lon0=0.0)                     # → (u, v) in [0, 1]
```

### Layer 3 — Overlays (matplotlib-friendly)

Every overlay returns plain x/y arrays in unit-disk coordinates (the
visible hemisphere, u²+v² ≤ 1) so you can `ax.plot(x, y)` them directly
onto a rendered disk — no Nx2 unpacking, no matplotlib dependency in the
overlay layer itself.

```python
graticule_segments(view_direction, up=(0,0,1),
                   lat_step_deg=30, lon_step_deg=30,
                   include_poles=True, samples_per_line=361)
    # → {"parallels": (xs, ys), "meridians": (xs, ys)}
    #   xs, ys are parallel LISTS of 1-D arrays — one polyline per line:
    #   for x, y in zip(*g["parallels"]): ax.plot(x, y)

limb_circle(samples=360)                           # → (x, y)  two 1-D arrays
subobserver_point(view_direction, up=(0,0,1))      # → (lat_deg, lon_deg) floats

terminator_segments(view_direction, sun_direction, up=(0,0,1), samples=361)
    # → (xs, ys)  parallel lists of 1-D arrays: the projected great
    #   circle {P : P · sun_unit = 0}, clipped at the limb.

flatmap_terminator(sun_direction, rotation_lon_deg=0.0, samples=721)
    # → (xs, ys) lon/lat-space terminator for render_flatmap output
```

### Layer 4 — Figure helper

```python
from implanet.figure import plot_planet

plot_planet(
    texture,
    view_direction=(-1, 0, 0),
    up=(0, 0, 1),
    sun_direction=None,
    ambient=0.1,
    size=720, margin=1.08, lon0=-math.pi,
    *,                                # keyword-only ↓
    title=None,
    body_name=None,
    source_text=None,                 # bottom-right attribution
    lat_step_deg=30.0, lon_step_deg=30.0,
    graticule_color="0.25",
    graticule_alpha=0.55,
    graticule_lw=0.7,
    show_limb=True,
    show_subobserver=True,
    show_terminator=True,             # only drawn if sun_direction is set
    terminator_color="white",
    terminator_lw=1.2,
    terminator_ls="--",
    terminator_alpha=0.95,
    figsize=(6.5, 6.5), dpi=150,
    ax=None,                          # plot into an existing axes if given
)   # → (fig, ax)
```

Produces:

- white background
- equirectangular disk via `imshow` with `extent=(-margin, +margin)`
- dashed parallel/meridian segments (every 30° by default), clipped at the limb
- black limb circle
- white dashed arc along the **day-night terminator** (the great circle
  where `P · sun_unit = 0`), clipped at the limb — only drawn when
  `sun_direction` is supplied
- red `+` at the sub-observer point
- ticks at `[-1, -0.5, 0, +0.5, +1]` labeled in planet radii
- caption: `sub-observer (lat, lon)` and (if `sun_direction` given) `sub-solar (lat, lon)`
- title and attribution slots

### Layer 5 — Ephemeris (optional)

```python
from implanet import (
    ensure_kernels, sun_direction, sub_solar_point,
    view_direction_from_earth, known_ephemeris_bodies,
)

ensure_kernels()                                   # one-time ~32 MB download
sun_direction(body, utc, abcorr="LT")              # → unit 3-vec in IAU_<body>
sub_solar_point(body, utc, abcorr="LT")            # → (lat_deg, lon_deg)
view_direction_from_earth(body, utc, abcorr="LT")  # → unit 3-vec in IAU_<body>
known_ephemeris_bodies()                           # list[str]
```

`body` is a name like `"Mars"`. `utc` is any SPICE-parseable string
(`"2026-05-14T12:00:00"`, `"2026 May 14 12:00:00"`, …). `abcorr` is the
NAIF aberration-correction code: `"NONE"`, `"LT"` (default — light-time),
or `"LT+S"` (light-time + stellar aberration).

Supported bodies (22): Sun's neighbors plus moons in DE440s' direct
coverage or close enough that the parent barycenter is a sufficient
proxy.

```
Mercury  Venus  Earth   Moon   Mars      Phobos   Deimos
Jupiter  Io     Europa  Ganymede Callisto
Saturn   Rhea   Iapetus Titan   Enceladus
Uranus   Neptune Triton  Pluto   Charon
```

The Sun is intentionally absent — `sun_direction("Sun", ...)` would be
meaningless; render the Sun's texture flat with `ambient=1.0`.

## Command line

```bash
implanet <texture> <output> [options]
```

`<texture>` is any image path; `<output>` is the PNG/JPG to write.

| Option | Default | Meaning |
|---|---|---|
| `--view x,y,z` | `-1,0,0` | camera → planet center |
| `--latlon lat,lon,0` | — | sub-camera point instead of `--view` (mutually exclusive) |
| `--up x,y,z` | `0,0,1` | up hint (north pole) |
| `--size N` | `512` | square edge length |
| `--margin F` | `1.05` | padding around the disk (≥1.0) |
| `--lon0 DEG` | `-180` | longitude of the texture's left edge |
| `--sun x,y,z` | none | planet → Sun; omit for flat (no shading) |
| `--ambient A` | `0.15` | night-side floor when `--sun` is set |
| `--background r,g,b` | `0,0,0` | off-disk fill (0–255) |

```bash
# Mars as seen from sub-point (20°N, 60°E), sun over the prime meridian
implanet $(python -c "import implanet;print(implanet.get_texture('Mars'))") \
         mars.png --latlon 20,60,0 --sun 1,0,0
```

## Map sources

`maps/manifest.json` catalogs equirectangular maps from NASA, ESA, JAXA,
and CNSA, plus a few community redistributions. Each entry has:

- `body` + `variant` (composite key — same body can appear multiple times)
- `agency`, `mission`, `instrument`, `description`
- `format`, `resolution`, `size_bytes_estimated`
- `asset_url` (auto-downloadable) and/or `portal_url` (manual)
- `provenance`, `license`, `citation`

**See what's available** (don't rely on a hand-maintained list here — it
goes stale; ask the package):

```python
import implanet
implanet.show_maps()                 # pretty table: body, variant, size, status
implanet.show_maps(body="Earth")     # filter to one body
implanet.list_maps(downloadable_only=True)   # → list[dict], for scripting
```

```bash
implanet-fetch --list                # same catalogue from the shell
implanet-fetch --where               # print the resolved maps directory
```

**Get one map** (lazy, on demand) — usually all you need:

```python
from implanet import get_texture
path = get_texture("Mars")                       # default variant
path = get_texture("Earth", "natural_earth3")    # specific, vivid variant
```

**Bulk-download** the auto-fetchable subset:

```bash
implanet-fetch                       # ~250 MB total
implanet-fetch --body Mars           # filter by body
implanet-fetch --agency NASA         # filter by agency
implanet-fetch --include-large       # also the multi-GB USGS mosaics
```

Status column meaning: `cached` (on disk) · `download` (auto-fetchable)
· `generate` (synthetic, built locally) · `manual` (portal-only — e.g.
Titan's default, ESA HRSC Mars, JAXA Kaguya, CNSA mosaics, full-res USGS;
`get_texture` raises with the portal URL for these).

## Reproducing the demo figures

Three independent scripts under `examples/`:

```bash
# 31 individual publication-style panels, one per local texture
python examples/scientific_figures.py
# → examples/figures_scientific/<body>_<variant>.png

# 5 side-by-side comparisons (Earth, Moon, Mars, Venus, Jupiter)
python examples/comparison_figures.py
# → examples/figures_comparison/<body>_variants.png

# Quick PIL-only rotation/terminator/pole grids, no matplotlib
python examples/figures.py
# → examples/figures/*.png
```

Pick a different epoch:

```bash
EPOCH="2025-12-21T18:00:00" python examples/scientific_figures.py
```

The `EPOCH` env var feeds straight into `spice.str2et`.

## Attribution & citation

`implanet` itself is MIT-licensed. The **maps and SPICE kernels** are
**not** our work — they're redistributions of public-domain or
Creative-Commons assets from NASA, ESA, JAXA, CNSA, USGS, and a few
community texture providers. The terms of those upstream sources apply.

**If you use any rendered figure in a paper or talk, credit both the
mission/instrument and the texture provider.** The manifest's `citation`
field gives the right phrasing per map; e.g.:

> Solar System Scope (CC BY 4.0). Underlying data: NASA MGS MOLA team;
> Viking Orbiter; USGS Astrogeology.

You can read the citation block at runtime so it stays in sync with the
catalogue:

```python
import implanet
implanet.show_attribution("Mars")    # one body, pretty-printed
implanet.show_attribution()          # all 41 entries
implanet.attribution("Earth", "natural_earth3")   # → dict
```

```bash
implanet-fetch --cite                # citation block from the CLI
implanet-fetch --cite --body Mars    # filtered
```

The first time `get_texture(body)` downloads a map, a one-line license
+ cite hint is printed to stderr so the requirement is hard to miss.

For the full block of every catalogued texture and SPICE kernel see
[`ATTRIBUTION.md`](ATTRIBUTION.md) at the repo root (regenerable via
`python scripts/build_attribution.py`).

## Tests

```bash
pip install -e .[all,test]
pytest tests/                       # 38 tests, ~1 s
```

`tests/test_render.py` covers basis orthonormality, disk geometry,
sphere→uv mapping, hemisphere correctness, terminator shading, and
path/PIL/array texture inputs. `tests/test_assets.py` covers the
registry/cache layer (resolution order, packaged-registry sync, the
synthetic texture). `tests/test_ephemeris.py` sanity-checks
SPICE-derived geometry against physical reality (Mercury obliquity ≈ 0,
Uranus obliquity dominates, sun near Greenwich at equinox noon UTC) and
auto-skips if `spiceypy` or the kernels are absent.

## File layout

```
implanet/
├── __init__.py            # public API + lazy ephemeris import
├── projection.py          # camera_basis, orthographic_rays, sphere_to_uv
├── render.py              # render_disk, render_flatmap
├── overlays.py            # graticule/limb/terminator/subobserver
├── figure.py              # plot_planet  (matplotlib)
├── ephemeris.py           # SPICE wrappers  (spiceypy)
├── fetch.py               # `implanet-fetch` console script
├── cli.py                 # `implanet` console script
└── assets/                # registry + lazy download/cache
    ├── __init__.py        #   get_texture, get_kernel, list_maps, show_maps
    ├── _registry.py _cache.py _synthetic.py
    └── data/              #   packaged copies of the registry JSON

maps/
├── manifest.json          # 41 entries, 23 bodies (textures)
├── kernels.json           # SPICE kernel registry
└── data/                  # texture cache (dev checkout)

kernels/                   # SPICE cache (dev checkout); pip → implanet/_data
scripts/                   # fetch_maps.py / sync_registry.py (dev shims)
examples/                  # demo.py, scientific_figures.py, flatmap_figures.py,
                           # transparent_disks.py, per-mission flybys, …
tests/                     # test_render.py, test_assets.py, test_ephemeris.py
```
