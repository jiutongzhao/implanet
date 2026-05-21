# Transparent disk views

Ready-to-use **RGBA** disks, one per body and illumination FOV, named `<body>_<view>.png`. Off-disk pixels are fully transparent (`alpha = 0`); the image spans exactly `x, y in [-1, 1]` (disk inscribed, row 0 = `y = +1`). Grab any file directly.

Sun fixed at +X (sub-solar at lon 0, equator); Lambertian-shaded, ambient 0.08 (the `antisun` view uses 0.3 so the night hemisphere stays readable).

| view | camera | shows |
|---|---|---|
| `sun` | Sun→body line | fully-lit dayside |
| `antisun` | opposite the Sun | night hemisphere (ambient only) |
| `terminator` | 90° from the Sun | day/night split down the middle |
| `north_pole` | down the +Z pole | pole-on, sun grazing one side |
| `south_pole` | down the −Z pole | pole-on |

Display with `interpolation='nearest'` (or composite over a background) to avoid blending the limb into the transparent pixels.

Bodies: Mercury, Venus, Earth, Moon, Mars, Phobos, Jupiter, Io, Europa, Ganymede, Callisto, Saturn, Enceladus, Rhea, Iapetus, Uranus, Neptune, Triton, Pluto, Charon

Skipped (manual-only / unavailable): Titan
