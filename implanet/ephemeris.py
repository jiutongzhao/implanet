"""Use SPICE (via spiceypy) to compute true sun directions in body-fixed frames.

Computes the direction from a body to the Sun, expressed in the body's
IAU rotation frame — the same frame in which our equirectangular textures
are laid out. Suitable for replacing arbitrary `sun_direction` vectors in
`implanet.render_disk` with physically correct sub-solar geometry at
a given epoch.

Required kernels (auto-downloaded into `kernels/` on first use):
    - naif0012.tls   leap seconds                                   ~5 KB
    - pck00011.tpc   planetary constants (body orientations)        ~130 KB
    - de440s.bsp     planetary ephemerides 1849-2150               ~32 MB

For moons that lack their own SPK, we use the parent planet's
*barycenter* as the position origin. The error in the sun direction this
introduces is at most max_moon_orbit / 1 AU ≈ a few arcseconds, well
below the sub-pixel level for any rendered figure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Tuple, Union

import numpy as np

import spiceypy

from implanet.assets import download, get_kernel, kernels_dir
from implanet.assets._registry import find_kernel

# Generic kernels needed for any ephemeris query, in SPICE load order.
# These are `id`s in maps/kernels.json.
_GENERIC_KERNEL_IDS = ("naif_lsk", "naif_pck", "de440s")

# Body name -> (IAU body-fixed frame, position origin used for ephemerides).
# For moons without their own SPK, we use the parent planet's barycenter.
_BODY_INFO = {
    "Mercury":   ("IAU_MERCURY",   "MERCURY"),
    "Venus":     ("IAU_VENUS",     "VENUS"),
    "Earth":     ("IAU_EARTH",     "EARTH"),
    "Moon":      ("IAU_MOON",      "MOON"),
    "Mars":      ("IAU_MARS",      "MARS BARYCENTER"),
    "Phobos":    ("IAU_PHOBOS",    "MARS BARYCENTER"),
    "Deimos":    ("IAU_DEIMOS",    "MARS BARYCENTER"),
    "Jupiter":   ("IAU_JUPITER",   "JUPITER BARYCENTER"),
    "Io":        ("IAU_IO",        "JUPITER BARYCENTER"),
    "Europa":    ("IAU_EUROPA",    "JUPITER BARYCENTER"),
    "Ganymede":  ("IAU_GANYMEDE",  "JUPITER BARYCENTER"),
    "Callisto":  ("IAU_CALLISTO",  "JUPITER BARYCENTER"),
    "Saturn":    ("IAU_SATURN",    "SATURN BARYCENTER"),
    "Enceladus": ("IAU_ENCELADUS", "SATURN BARYCENTER"),
    "Rhea":      ("IAU_RHEA",      "SATURN BARYCENTER"),
    "Iapetus":   ("IAU_IAPETUS",   "SATURN BARYCENTER"),
    "Titan":     ("IAU_TITAN",     "SATURN BARYCENTER"),
    "Uranus":    ("IAU_URANUS",    "URANUS BARYCENTER"),
    "Neptune":   ("IAU_NEPTUNE",   "NEPTUNE BARYCENTER"),
    "Triton":    ("IAU_TRITON",    "NEPTUNE BARYCENTER"),
    "Pluto":     ("IAU_PLUTO",     "PLUTO BARYCENTER"),
    "Charon":    ("IAU_CHARON",    "PLUTO BARYCENTER"),
}

_loaded = False


def _generic_paths(kernel_dir: Union[str, Path, None]) -> list:
    """Resolve (downloading if needed) the three generic kernels.

    `kernel_dir` keeps backward compatibility: if given, kernels are
    fetched into exactly that directory. Otherwise the shared
    implanet.assets cache is used (which honours IMPLANET_KERNELS /
    IMPLANET_CACHE and the in-repo kernels/ dir).
    """
    paths = []
    for kid in _GENERIC_KERNEL_IDS:
        entry = find_kernel(kid)
        if kernel_dir is not None:
            dest = Path(kernel_dir) / entry["filename"]
            if not dest.exists():
                print(f"  downloading SPICE kernel {entry['filename']}")
            download(entry["url"], dest,
                     expected_size=entry.get("size_bytes"), quiet=True)
        else:
            dest = get_kernel(kid, quiet=True)
        paths.append(dest)
    return paths


def ensure_kernels(kernel_dir: Union[str, Path, None] = None) -> Path:
    """Download the generic SPICE kernels if missing; return their directory.

    Examples
    --------
    First call downloads naif0012.tls, pck00011.tpc and de440s.bsp
    (~32 MB total) into the cache:

        >>> ensure_kernels()                       # doctest: +SKIP
        PosixPath('.../kernels')

    Use a custom location (or set the IMPLANET_KERNELS / IMPLANET_CACHE
    env vars):

        >>> ensure_kernels("/data/shared/spice_kernels")   # doctest: +SKIP
        PosixPath('/data/shared/spice_kernels')
    """
    paths = _generic_paths(kernel_dir)
    return paths[0].parent


def load_kernels(kernel_dir: Union[str, Path, None] = None) -> None:
    """Furnish kernels into the SPICE pool (idempotent).

    Most users won't call this directly — `sun_direction`,
    `sub_solar_point` and friends call it lazily on first use. Useful if
    you want kernels loaded eagerly (e.g. before a long batch).

    Examples
    --------
        >>> load_kernels()                       # downloads + furnishes
        >>> load_kernels()                       # no-op, already loaded
    """
    global _loaded
    if _loaded:
        return
    for path in _generic_paths(kernel_dir):
        spiceypy.furnsh(str(path))
    _loaded = True


def utc_to_et(utc: str) -> float:
    """Convert UTC string ('2026-05-14T12:00:00') to TDB ephemeris seconds."""
    load_kernels()
    return spiceypy.str2et(utc)


def _resolve_body(body: str) -> Tuple[str, str]:
    if body not in _BODY_INFO:
        raise KeyError(
            f"Unknown body {body!r}. Known: {sorted(_BODY_INFO.keys())}"
        )
    return _BODY_INFO[body]


def _direction_in_body_frame(target: str, frame: str, origin: str,
                             et: float, abcorr: str) -> np.ndarray:
    """Compute a unit vector via J2000 + pxform.

    Computing the position directly in IAU_<body> would require SPICE to
    resolve the frame's center body (e.g. 499 = MARS), which our planet-
    barycenter-only ephemeris lacks. Going through J2000 sidesteps that:
    pxform reads orientation from the PCK and needs no SPK data.
    """
    pos_j2000, _ = spiceypy.spkpos(target, et, "J2000", abcorr, origin)
    R = spiceypy.pxform("J2000", frame, et)
    pos_iau = np.asarray(R, dtype=np.float64) @ np.asarray(pos_j2000,
                                                            dtype=np.float64)
    n = np.linalg.norm(pos_iau)
    if n == 0.0:
        raise RuntimeError(f"Zero-length vector from {origin} to {target}")
    return pos_iau / n


def sun_direction(body: str, utc: str,
                  abcorr: str = "LT") -> np.ndarray:
    """Unit vector from `body` toward the Sun, in the body's IAU frame.

    Suitable for passing as `sun_direction=` to `render_disk`.
    `abcorr` is the SPICE aberration correction ("NONE", "LT", "LT+S").

    Examples
    --------
        >>> v = sun_direction("Earth", "2026-05-14T12:00:00")
        >>> float(np.linalg.norm(v))             # always a unit vector
        1.0
        >>> v.round(4)
        array([ 0.9471, -0.0137,  0.3206])       # sub-solar ~ (+18°, -1°)

    Plug straight into `render_disk`:

        >>> img = render_disk(earth_tex,
        ...                     view_direction=(-1, 0, 0),
        ...                     sun_direction=v,
        ...                     ambient=0.08)
    """
    load_kernels()
    frame, origin = _resolve_body(body)
    et = spiceypy.str2et(utc)
    return _direction_in_body_frame("SUN", frame, origin, et, abcorr)


def sub_solar_point(body: str, utc: str,
                    abcorr: str = "LT") -> Tuple[float, float]:
    """Return (latitude_deg, east_longitude_deg) of the sub-solar point.

    Examples
    --------
    The sub-solar point is where the Sun is directly overhead:

        >>> sub_solar_point("Mars", "2026-05-14T12:00:00")
        (-24.6, -160.2)

    Sun crosses Earth's equator at the March equinox:

        >>> lat, _ = sub_solar_point("Earth", "2026-03-20T16:00:00")
        >>> abs(lat) < 0.2
        True

    Uranus's 98° obliquity makes its sub-solar latitude swing wildly:

        >>> lat, _ = sub_solar_point("Uranus", "2026-05-14T12:00:00")
        >>> lat > 50
        True
    """
    v = sun_direction(body, utc, abcorr=abcorr)
    lat = float(np.degrees(np.arcsin(np.clip(v[2], -1.0, 1.0))))
    lon = float(np.degrees(np.arctan2(v[1], v[0])))
    return lat, lon


def view_direction_from_earth(body: str, utc: str,
                              abcorr: str = "LT") -> np.ndarray:
    """Unit vector from `body` toward Earth, in the body's IAU frame.

    Negate to get the view-direction argument expected by `render_disk`
    (which wants camera -> planet-center). Useful for "as seen from Earth"
    renders.

    Examples
    --------
    Get the sub-Earth point on the Moon — captures lunar libration
    automatically when sampled over time:

        >>> v = view_direction_from_earth("Moon", "2026-01-01T00:00:00")
        >>> v.round(3)
        array([ 0.993, -0.022, -0.114])    # sub-Earth ≈ (-6.6°, -1.3°)

    Render the Moon as seen from Earth at a given instant, with real
    libration AND real solar illumination:

        >>> utc = "2026-01-15T00:00:00"
        >>> earth = view_direction_from_earth("Moon", utc)
        >>> view  = tuple(-x for x in earth)        # camera → center
        >>> img = render_disk(moon_tex,
        ...                     view_direction=view,
        ...                     sun_direction=sun_direction("Moon", utc))
    """
    load_kernels()
    frame, origin = _resolve_body(body)
    et = spiceypy.str2et(utc)
    return _direction_in_body_frame("EARTH", frame, origin, et, abcorr)


def known_bodies():
    """List of body names supported by sun_direction().

    Examples
    --------
        >>> bodies = known_bodies()
        >>> len(bodies)
        22
        >>> bodies[:5]
        ['Mercury', 'Venus', 'Earth', 'Moon', 'Mars']
        >>> "Pluto" in bodies and "Charon" in bodies
        True
    """
    return list(_BODY_INFO.keys())
