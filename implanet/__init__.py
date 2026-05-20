"""Render a planet's equirectangular map into a 2D view from a given direction."""

from implanet.render import render_disk, render_flatmap, render_info
from implanet.projection import camera_basis, orthographic_rays, sphere_to_uv
from implanet.overlays import (
    flatmap_terminator,
    graticule_segments,
    limb_circle,
    subobserver_point,
    terminator_segments,
)
from implanet.assets import (
    attribution,
    get_texture,
    kernel_license_notes,
    list_maps,
    show_attribution,
    show_maps,
    texture_license_notes,
)

__all__ = [
    "render_disk",
    "render_flatmap",
    "render_info",
    "camera_basis",
    "orthographic_rays",
    "sphere_to_uv",
    "graticule_segments",
    "limb_circle",
    "subobserver_point",
    "terminator_segments",
    "flatmap_terminator",
    "get_texture",
    "list_maps",
    "show_maps",
    "attribution",
    "show_attribution",
    "texture_license_notes",
    "kernel_license_notes",
]

# Ephemeris support requires the optional `spiceypy` dependency. Import
# lazily so the rest of the package keeps working without it.
try:
    from implanet.ephemeris import (
        sun_direction,
        sub_solar_point,
        view_direction_from_earth,
        ensure_kernels,
        load_kernels,
        known_bodies as known_ephemeris_bodies,
    )
    __all__ += [
        "sun_direction",
        "sub_solar_point",
        "view_direction_from_earth",
        "ensure_kernels",
        "load_kernels",
        "known_ephemeris_bodies",
    ]
except ImportError:
    pass
__version__ = "0.1.0"
