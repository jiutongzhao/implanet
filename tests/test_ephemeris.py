"""Smoke tests for the optional SPICE-driven ephemeris module.

Skipped automatically if spiceypy or the cached kernels are missing.
"""

import numpy as np
import pytest

spice = pytest.importorskip("spiceypy")
from implanet import ephemeris


KERNEL_DIR = ephemeris.KERNEL_DIR


@pytest.fixture(scope="module", autouse=True)
def _kernels():
    if not all((KERNEL_DIR / k).exists() for k in ephemeris._KERNELS):
        pytest.skip("SPICE kernels not yet downloaded; run ensure_kernels()")
    ephemeris.load_kernels()


def test_sun_direction_unit_norm():
    v = ephemeris.sun_direction("Earth", "2026-05-14T12:00:00")
    np.testing.assert_allclose(np.linalg.norm(v), 1.0, atol=1e-12)


def test_earth_sub_solar_near_greenwich_at_noon_utc():
    """At 12:00 UTC the sun should be near 0° longitude (within 5° for
    equation-of-time effects)."""
    lat, lon = ephemeris.sub_solar_point("Earth", "2026-03-21T12:00:00")
    assert abs(lon) < 5.0
    assert abs(lat) < 2.0  # near equinox


def test_mercury_sub_solar_lat_near_zero():
    """Mercury's spin axis is nearly perpendicular to its orbit."""
    lat, _ = ephemeris.sub_solar_point("Mercury", "2026-05-14T12:00:00")
    assert abs(lat) < 1.5


def test_jupiter_sub_solar_lat_within_tilt():
    """Jupiter's obliquity is ~3°, so the sub-solar latitude stays small."""
    lat, _ = ephemeris.sub_solar_point("Jupiter", "2026-05-14T12:00:00")
    assert abs(lat) < 5.0


def test_uranus_sub_solar_lat_can_be_large():
    """Uranus's 98° obliquity means the sub-solar latitude swings widely."""
    lat, _ = ephemeris.sub_solar_point("Uranus", "2026-05-14T12:00:00")
    # Around 2026 the southern hemisphere is moving toward the Sun;
    # the latitude is large in magnitude.
    assert abs(lat) > 50.0


def test_known_bodies_contains_planets_and_some_moons():
    names = set(ephemeris.known_bodies())
    for x in ("Earth", "Mars", "Jupiter", "Io", "Europa", "Phobos",
              "Enceladus", "Triton"):
        assert x in names
