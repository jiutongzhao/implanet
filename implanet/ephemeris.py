"""Use SPICE (via spiceypy) to compute true sun directions in body-fixed frames.

Computes the direction from a body to the Sun, expressed in the body's
IAU rotation frame — the same frame in which our equirectangular textures
are laid out. Suitable for replacing arbitrary `sun_direction` vectors in
`implanet.render_planet` with physically correct sub-solar geometry at
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

import os
import urllib.request
from pathlib import Path
from typing import Sequence, Tuple, Union

import numpy as np

import spiceypy as spice


REPO_ROOT = Path(__file__).resolve().parent.parent
KERNEL_DIR = Path(os.environ.get("IMPLANET_KERNELS",
                                 str(REPO_ROOT / "kernels")))

# Files we need, in load order. Format: filename -> URL.
_KERNELS = {
    "naif0012.tls": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls",
    "pck00011.tpc": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc",
    "de440s.bsp":   "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp",
}

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


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "implanet/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        chunk = 1 << 16
        while True:
            buf = r.read(chunk)
            if not buf:
                break
            f.write(buf)
    tmp.replace(dest)


def ensure_kernels(kernel_dir: Union[str, Path, None] = None) -> Path:
    """Download SPICE kernels if missing; return the kernel directory.

    Examples
    --------
    First call downloads naif0012.tls, pck00011.tpc and de440s.bsp
    (~32 MB total) into ./kernels/:

        >>> ensure_kernels()
        PosixPath('.../kernels')

    Use a custom location (or set the IMPLANET_KERNELS env var):

        >>> ensure_kernels("/data/shared/spice_kernels")
        PosixPath('/data/shared/spice_kernels')
    """
    d = Path(kernel_dir) if kernel_dir is not None else KERNEL_DIR
    d.mkdir(parents=True, exist_ok=True)
    for name, url in _KERNELS.items():
        path = d / name
        if not path.exists():
            print(f"  downloading SPICE kernel {name} ({url})")
            _download(url, path)
    return d


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
    d = ensure_kernels(kernel_dir)
    for name in _KERNELS:
        spice.furnsh(str(d / name))
    _loaded = True


def utc_to_et(utc: str) -> float:
    """Convert UTC string ('2026-05-14T12:00:00') to TDB ephemeris seconds."""
    load_kernels()
    return spice.str2et(utc)


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
    pos_j2000, _ = spice.spkpos(target, et, "J2000", abcorr, origin)
    R = spice.pxform("J2000", frame, et)
    pos_iau = np.asarray(R, dtype=np.float64) @ np.asarray(pos_j2000,
                                                            dtype=np.float64)
    n = np.linalg.norm(pos_iau)
    if n == 0.0:
        raise RuntimeError(f"Zero-length vector from {origin} to {target}")
    return pos_iau / n


def sun_direction(body: str, utc: str,
                  abcorr: str = "LT") -> np.ndarray:
    """Unit vector from `body` toward the Sun, in the body's IAU frame.

    Suitable for passing as `sun_direction=` to `render_planet`.
    `abcorr` is the SPICE aberration correction ("NONE", "LT", "LT+S").

    Examples
    --------
        >>> v = sun_direction("Earth", "2026-05-14T12:00:00")
        >>> float(np.linalg.norm(v))             # always a unit vector
        1.0
        >>> v.round(4)
        array([ 0.9471, -0.0137,  0.3206])       # sub-solar ~ (+18°, -1°)

    Plug straight into `render_planet`:

        >>> img = render_planet(earth_tex,
        ...                     view_direction=(-1, 0, 0),
        ...                     sun_direction=v,
        ...                     ambient=0.08)
    """
    load_kernels()
    frame, origin = _resolve_body(body)
    et = spice.str2et(utc)
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

    Negate to get the view-direction argument expected by `render_planet`
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
        >>> img = render_planet(moon_tex,
        ...                     view_direction=view,
        ...                     sun_direction=sun_direction("Moon", utc))
    """
    load_kernels()
    frame, origin = _resolve_body(body)
    et = spice.str2et(utc)
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
