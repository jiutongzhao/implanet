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
    kernel_license_notes,
    kernel_registry,
    texture_entries,
    texture_license_notes,
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
    "attribution",
    "show_attribution",
    "texture_license_notes",
    "kernel_license_notes",
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

    Downloads it into the maps cache on first use. Raises with an
    actionable hint if the manifest entry is manual-only (no
    ``asset_url``) or if ``download_if_missing=False`` and the file
    isn't cached yet.
    """
    e = find_texture(body, variant)
    url = e.get("asset_url")
    generator = e.get("generator")
    fname = e.get("filename") or (url.rsplit("/", 1)[-1] if url else None)
    if not fname:
        raise ValueError(_manual_download_hint(e))
    dest = maps_dir() / fname
    if dest.exists():
        return dest
    if generator:
        # Procedurally generated — local and free, so build regardless
        # of download_if_missing.
        from implanet.assets._synthetic import build
        return build(generator, dest)
    if not download_if_missing:
        raise FileNotFoundError(_download_disabled_hint(e, dest))
    if not url:
        raise ValueError(_manual_download_hint(e))
    path = download(url, dest,
                    expected_size=e.get("size_bytes_estimated"), quiet=quiet)
    if not quiet:
        _print_citation_hint(e)
    return path


def _manual_download_hint(entry: dict) -> str:
    """Multi-line, actionable error for a manual-only texture: tells the
    user where to download it from, what filename to save it as, and
    which directory to drop it into so the next ``get_texture()`` call
    just works."""
    body = entry.get("body", "?")
    variant = entry.get("variant") or "(default)"
    portal = entry.get("portal_url") or "<no portal URL in registry>"
    fname = (entry.get("filename")
             or (entry["asset_url"].rsplit("/", 1)[-1]
                 if entry.get("asset_url") else "<see portal>"))
    target_dir = maps_dir()
    note = entry.get("note", "")
    note_line = f"\n  Note: {note}" if note else ""
    return (
        f"Texture {body}/{variant} is manual-only — the registry has "
        f"no direct download URL, so implanet can't fetch it for you.\n"
        f"\n"
        f"To use it:\n"
        f"  1. Download from: {portal}\n"
        f"  2. Save it as:    {fname}\n"
        f"  3. Place it in:   {target_dir}\n"
        f"\n"
        f"Then re-run your get_texture({body!r}"
        + (f", {entry['variant']!r}" if entry.get('variant') else "")
        + ") call — the file will be picked up from the cache."
        + note_line
        + f"\n\nFull license/citation: "
        f"implanet.show_attribution({body!r})"
    )


def _download_disabled_hint(entry: dict, dest: Path) -> str:
    """Error for `download_if_missing=False` when the file isn't cached
    yet — tells the user three ways to get it onto disk."""
    body = entry.get("body", "?")
    variant = entry.get("variant") or "(default)"
    var_arg = (f", {entry['variant']!r}" if entry.get('variant') else "")
    return (
        f"Texture {body}/{variant} isn't cached at {dest} and "
        f"download_if_missing=False was set.\n"
        f"\n"
        f"To populate the cache, pick one:\n"
        f"  • Python: implanet.get_texture({body!r}{var_arg}) "
        f"   (default download_if_missing=True will fetch it)\n"
        f"  • CLI:    implanet-fetch --body {body}\n"
        f"  • Manual: drop the file at {dest} yourself"
    )


def _print_citation_hint(entry: dict) -> None:
    """One-line license + citation note, printed to stderr on a fresh
    texture download so users don't miss attribution requirements."""
    import sys
    lic = entry.get("license") or "see registry"
    cite = entry.get("citation") or entry.get("provenance") or ""
    body = entry.get("body", "?")
    variant = entry.get("variant", "")
    head = f"[implanet] {body}/{variant} license: {lic}"
    print(head, file=sys.stderr)
    if cite:
        print(f"[implanet] cite: {cite}", file=sys.stderr)
    print("[implanet] full attribution: implanet.show_attribution"
          f"({body!r})", file=sys.stderr)


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


def attribution(body: str, variant: Optional[str] = None) -> dict:
    """Return the citation / license info for a texture.

    Pulled directly from ``maps/manifest.json`` so it stays in sync with
    the catalogue. The returned dict has these fields (any may be empty
    if the registry doesn't supply them):

      ``body, variant, agency, mission, instrument, provenance,
      license, citation, portal_url, asset_url, note,
      umbrella_license_notes``

    The last field is the top-level note that applies to *all* textures
    (agency-level terms — e.g. NASA public domain, ESA CC BY-SA 3.0
    IGO, JAXA-specific terms). Cite **both** the texture provider and
    the underlying mission/instrument when publishing.

    Examples
    --------
        >>> from implanet import attribution
        >>> a = attribution("Mars")
        >>> a["license"], a["citation"]      # doctest: +SKIP
    """
    e = find_texture(body, variant)
    return {
        "body": e.get("body"),
        "variant": e.get("variant"),
        "agency": e.get("agency"),
        "mission": e.get("mission"),
        "instrument": e.get("instrument"),
        "provenance": e.get("provenance"),
        "license": e.get("license"),
        "citation": e.get("citation"),
        "portal_url": e.get("portal_url"),
        "asset_url": e.get("asset_url"),
        "note": e.get("note"),
        "umbrella_license_notes": texture_license_notes(),
    }


def show_attribution(body: Optional[str] = None) -> None:
    """Print the citation / license block for one body, or for all
    textures if ``body`` is None.

    Use this *before publishing* any figure made with implanet — the
    text shown is what you should reproduce (or paraphrase) as the
    figure source line, plus the upstream mission credit.

    Examples
    --------
        >>> import implanet
        >>> implanet.show_attribution("Mars")
        >>> implanet.show_attribution()      # all entries
    """
    notes = texture_license_notes()
    if notes:
        print("UMBRELLA LICENSE NOTES")
        print("-" * 22)
        # Wrap the umbrella note to ~80 cols for readability.
        import textwrap
        for line in textwrap.wrap(notes, width=78):
            print(line)
        print()

    entries = list(texture_entries())
    if body:
        body_l = body.lower()
        entries = [e for e in entries if e["body"].lower() == body_l]
        if not entries:
            raise KeyError(f"No texture for body {body!r} in manifest.json")

    for e in entries:
        head = f"{e['body']} / {e.get('variant', '')}"
        print(head)
        print("=" * len(head))
        for key in ("agency", "mission", "instrument", "provenance",
                    "license", "citation", "portal_url", "note"):
            v = e.get(key)
            if v:
                print(f"  {key:<11}: {v}")
        print()
