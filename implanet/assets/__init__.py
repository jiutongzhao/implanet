"""Lazy, cached access to implanet's external assets.

Two asset families, two registries:

* **textures** — equirectangular body maps, catalogued in
  ``maps/manifest.json``.
* **kernels**  — NAIF SPICE kernels, catalogued in ``maps/kernels.json``.

Nothing is bundled in the wheel; assets are downloaded on first use into
a user cache (override with ``IMPLANET_CACHE``; in a dev checkout the
repo's ``maps/data`` and ``kernels`` dirs are reused automatically). See
``implanet.assets._cache`` for the full resolution order.

Typical use::

    from implanet.assets import get_texture, get_kernel
    tex = get_texture("Mars")                 # -> Path, downloads if needed
    spk = get_kernel("voyager2_neptune")      # -> Path, downloads if needed
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from implanet.assets._cache import (
    _human,
    cache_base,
    download,
    kernels_dir,
    maps_dir,
)
from implanet.assets._registry import (
    find_kernel,
    find_texture,
    kernel_entries,
    kernel_registry,
    texture_entries,
    texture_registry,
)

__all__ = [
    "get_texture",
    "get_kernel",
    "texture_path",
    "kernel_path",
    "cache_base",
    "kernels_dir",
    "maps_dir",
    "texture_registry",
    "kernel_registry",
    "texture_entries",
    "kernel_entries",
    "find_texture",
    "find_kernel",
    "list_maps",
    "show_maps",
]


def kernel_path(key: str) -> Path:
    """Where kernel `key` (id or filename) would live in the cache."""
    e = find_kernel(key)
    sub = e.get("subdir", "")
    base = kernels_dir()
    return (base / sub / e["filename"]) if sub else (base / e["filename"])


def texture_path(body: str, variant: Optional[str] = None) -> Path:
    """Where the texture for `body` (+ optional variant) would live."""
    e = find_texture(body, variant)
    fname = e.get("filename") or e["asset_url"].rsplit("/", 1)[-1]
    return maps_dir() / fname


def get_kernel(key: str, *, download_if_missing: bool = True,
                quiet: bool = False) -> Path:
    """Return a local path to SPICE kernel `key` (id or filename).

    Downloads it into the kernels cache on first use unless
    ``download_if_missing=False`` (then a missing file raises).
    """
    e = find_kernel(key)
    dest = kernel_path(key)
    if dest.exists():
        return dest
    if not download_if_missing:
        raise FileNotFoundError(
            f"Kernel {key!r} not cached at {dest} and download disabled."
        )
    return download(e["url"], dest,
                    expected_size=e.get("size_bytes"), quiet=quiet)


def get_texture(body: str, variant: Optional[str] = None, *,
                download_if_missing: bool = True,
                quiet: bool = False) -> Path:
    """Return a local path to the texture for `body` (+ optional variant).

    Downloads it into the maps cache on first use. Raises if the manifest
    entry is manual-only (no ``asset_url``).
    """
    e = find_texture(body, variant)
    url = e.get("asset_url")
    generator = e.get("generator")
    fname = e.get("filename") or (url.rsplit("/", 1)[-1] if url else None)
    if not fname:
        raise ValueError(
            f"Texture {body}/{e.get('variant')} is manual-only "
            f"(no asset_url). Obtain it from: {e.get('portal_url')}"
        )
    dest = maps_dir() / fname
    if dest.exists():
        return dest
    if generator:
        # Procedurally generated — local and free, so build regardless
        # of download_if_missing.
        from implanet.assets._synthetic import build
        return build(generator, dest)
    if not download_if_missing:
        raise FileNotFoundError(
            f"Texture {body}/{variant} not cached at {dest} and download "
            f"disabled."
        )
    if not url:
        raise ValueError(
            f"Texture {body}/{e.get('variant')} is manual-only "
            f"(no asset_url). Obtain it from: {e.get('portal_url')}"
        )
    return download(url, dest,
                    expected_size=e.get("size_bytes_estimated"), quiet=quiet)


def _status(entry: dict, cached: bool) -> str:
    if cached:
        return "cached"
    if entry.get("generator"):
        return "generate"
    if entry.get("asset_url"):
        return "download"
    return "manual"


def list_maps(body: Optional[str] = None,
              downloadable_only: bool = False) -> list:
    """Return a list of dicts summarising every texture in the registry.

    Each dict: ``body, variant, agency, mission, resolution, format,
    size_bytes, status`` (``cached`` / ``download`` / ``generate`` /
    ``manual``), ``cached`` (bool), ``filename``, ``path``.

    Examples
    --------
        >>> from implanet import list_maps
        >>> [m['variant'] for m in list_maps(body='Mars')]
        ['sss', 'viking_mdim21_1km', ...]
    """
    out = []
    for e in texture_entries():
        if body and e["body"].lower() != body.lower():
            continue
        url = e.get("asset_url")
        downloadable = bool(url) or bool(e.get("generator"))
        if downloadable_only and not downloadable:
            continue
        fname = e.get("filename") or (url.rsplit("/", 1)[-1] if url else None)
        path = (maps_dir() / fname) if fname else None
        cached = bool(path and path.exists())
        out.append({
            "body": e["body"],
            "variant": e.get("variant"),
            "agency": e.get("agency"),
            "mission": e.get("mission"),
            "resolution": e.get("resolution"),
            "format": e.get("format"),
            "size_bytes": e.get("size_bytes_estimated"),
            "status": _status(e, cached),
            "cached": cached,
            "filename": fname,
            "path": str(path) if path else None,
        })
    return out


def show_maps(body: Optional[str] = None,
              downloadable_only: bool = False) -> None:
    """Print a table of every available texture map.

    Status column: ``cached`` (already on disk), ``download``
    (auto-fetchable), ``generate`` (synthetic, built locally),
    ``manual`` (portal-only). Filter with `body=` /
    `downloadable_only=`.

    Examples
    --------
        >>> import implanet
        >>> implanet.show_maps()
        >>> implanet.show_maps(body='Earth')
    """
    rows = list_maps(body, downloadable_only)
    print(f"{len(rows)} map(s)  (cache dir: {maps_dir()})\n")
    hdr = f"{'BODY':<10} {'VARIANT':<26} {'AGENCY':<9} {'RES':<11} {'SIZE':<9} STATUS"
    print(hdr)
    print("-" * len(hdr))
    for m in rows:
        size = "-" if m["size_bytes"] is None else _human(m["size_bytes"])
        print(f"{m['body']:<10} {str(m['variant'] or ''):<26} "
              f"{str(m['agency'] or ''):<9} {str(m['resolution'] or ''):<11} "
              f"{size:<9} {m['status']}")
