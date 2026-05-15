"""Command-line interface: implanet <texture> <output> [options]."""

from __future__ import annotations

import argparse
import math

import numpy as np
from PIL import Image

from implanet.render import render_planet


def _vec3(s: str):
    parts = [float(x) for x in s.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("expected three comma-separated floats")
    return tuple(parts)


def _direction_from_lat_lon(lat_deg: float, lon_deg: float):
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    # Vector pointing FROM camera TOWARD planet center =
    # negative of the surface normal at (lat, lon).
    x = math.cos(lat) * math.cos(lon)
    y = math.cos(lat) * math.sin(lon)
    z = math.sin(lat)
    return (-x, -y, -z)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="implanet",
        description="Render a planet's equirectangular map into a 2D view.",
    )
    p.add_argument("texture", help="Path to equirectangular texture image.")
    p.add_argument("output", help="Path for the rendered PNG/JPG.")

    direction = p.add_mutually_exclusive_group()
    direction.add_argument(
        "--view", type=_vec3, default=None,
        help="View direction as 'x,y,z' (camera -> planet center).",
    )
    direction.add_argument(
        "--latlon", type=_vec3, default=None, metavar="LAT,LON,_",
        help="Sub-camera point on the planet as 'lat_deg,lon_deg,0' "
             "(third value ignored). Convenience for `--view`.",
    )

    p.add_argument("--up", type=_vec3, default=(0.0, 0.0, 1.0),
                   help="Up hint vector (default: 0,0,1 = north pole).")
    p.add_argument("--size", type=int, default=512, help="Output image edge length.")
    p.add_argument("--margin", type=float, default=1.05,
                   help="Padding factor around the disk (>=1.0).")
    p.add_argument("--lon0", type=float, default=-180.0,
                   help="Longitude (deg) of the texture's left edge.")
    p.add_argument("--sun", type=_vec3, default=None,
                   help="Sun direction 'x,y,z' (planet -> sun). Omit for flat shading.")
    p.add_argument("--ambient", type=float, default=0.15,
                   help="Ambient light when --sun is used.")
    p.add_argument("--background", type=_vec3, default=(0.0, 0.0, 0.0),
                   help="Background RGB 0-255 as 'r,g,b'.")
    args = p.parse_args(argv)

    if args.latlon is not None:
        view = _direction_from_lat_lon(args.latlon[0], args.latlon[1])
    elif args.view is not None:
        view = args.view
    else:
        view = (-1.0, 0.0, 0.0)  # default: looking at lat=0, lon=0

    tex = Image.open(args.texture)
    img = render_planet(
        tex,
        view_direction=view,
        up=args.up,
        size=args.size,
        margin=args.margin,
        lon0=math.radians(args.lon0),
        sun_direction=args.sun,
        ambient=args.ambient,
        background=tuple(int(c) for c in args.background),
    )
    img.save(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
