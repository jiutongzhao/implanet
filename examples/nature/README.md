# `examples/nature/` — the publication figure series

Scripts that re-plot the `examples/` demos as publication-grade,
image-plate figures (raster planet disks + editable vector overlays and
text). Outputs land in [`figures/nature/`](../../figures/nature/).

```bash
python examples/nature/make_all.py        # all six plates
python examples/nature/fig03_illumination.py   # just one
```

Each plate saves a light `.png` preview plus editable `.pdf`/`.svg`
masters (300 dpi, text kept as `<text>` nodes for assembly in
Illustrator / Inkscape).

| File | Plate |
|---|---|
| `_style.py` | shared rcParams, palette, disk-axes + overlay helpers, the saver |
| `fig01_frame_and_projection.py` | frame & `view_direction` convention (synthetic map, no download) |
| `fig02_viewing_geometry.py` | one `view_direction` → any vantage (Earth) |
| `fig03_illumination.py` | `sun_direction` shading: phase sweep + named FOVs (Moon) |
| `fig04_earth_spice.py` | SPICE geometry: sunlit disk + flat-map terminator |
| `fig05_texture_gallery.py` | every catalogued body's default map |
| `fig06_variant_comparison.py` | catalogued variants per body |
| `make_all.py` | run every plate in order |

The mapping from each plate back to the demo it supersedes is in
[`figures/nature/README.md`](../../figures/nature/README.md). These
scripts route every texture through `get_texture()` and every overlay
through the package's public API, so they double as worked usage
examples.
