"""Bulk-download equirectangular planet maps (``implanet-fetch``).

Entries with a non-null ``asset_url`` are downloaded automatically;
``portal_url``-only entries are reported as "manual". Destination honours
IMPLANET_MAPS / IMPLANET_CACHE, then the in-repo ``maps/data`` (dev
checkout), then ``site-packages/implanet/_data/maps`` (pip default).

Usage
-----
    implanet-fetch                # download all auto entries
    implanet-fetch --list         # show every entry's status
    implanet-fetch --body Moon    # filter
    implanet-fetch --include-large  # allow files >200 MB
    implanet-fetch --where        # print the resolved maps directory
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
from pathlib import Path

from implanet.assets import maps_dir
from implanet.assets._cache import _human, download
from implanet.assets._registry import texture_entries, texture_license_notes

LARGE_THRESHOLD = 200 * 1024 * 1024  # 200 MB


def _filter(entries, body=None, variant=None, agency=None):
    out = entries
    if body:
        out = [e for e in out if e["body"].lower() == body.lower()]
    if variant:
        out = [e for e in out if e.get("variant", "").lower() == variant.lower()]
    if agency:
        out = [e for e in out if e["agency"].lower() == agency.lower()]
    return out


def download_maps(body=None, variant=None, agency=None, *,
                  include_large=False, quiet=False):
    """Bulk-download maps from Python — the importable counterpart to the
    ``implanet-fetch`` CLI.

    Downloads every auto-fetchable (and synthetic) texture matching the
    filters into the maps cache and returns a ``list[Path]`` of the local
    files (already-cached ones included). Manual-only entries are skipped,
    as are files larger than ~200 MB unless ``include_large=True``.

    Parameters
    ----------
    body, variant, agency : str, optional
        Case-insensitive filters; omit for "everything".
    include_large : bool
        Allow files above the 200 MB threshold (e.g. the multi-GB USGS
        full-res mosaics).
    quiet : bool
        Suppress per-file download progress + the license/cite hint.

    Examples
    --------
        >>> from implanet import download_maps
        >>> download_maps(body="Mars")             # every Mars variant
        >>> paths = download_maps(agency="NASA")   # → list[Path]
        >>> download_maps()                        # the whole catalogue
    """
    from implanet.assets import get_texture       # local: reuse all the
                                                  # download/generator logic
    entries = _filter(texture_entries(), body=body, variant=variant,
                      agency=agency)
    out = []
    for e in entries:
        if not (e.get("asset_url") or e.get("generator")):
            continue                              # manual-only → skip
        sz = e.get("size_bytes_estimated")
        if not include_large and sz and sz > LARGE_THRESHOLD:
            if not quiet:
                print(f"  skip {e['body']}/{e.get('variant')}: "
                      f"{_human(sz)} (> {_human(LARGE_THRESHOLD)}; "
                      f"pass include_large=True)", file=sys.stderr)
            continue
        try:
            out.append(get_texture(e["body"], e.get("variant"), quiet=quiet))
        except Exception as exc:                  # network / decode / etc.
            if not quiet:
                print(f"  FAILED {e['body']}/{e.get('variant')}: {exc}",
                      file=sys.stderr)
    return out


def cmd_list(entries):
    print(f"{'BODY':<10} {'VARIANT':<26} {'AGENCY':<10} {'SIZE':<10} STATUS")
    print("-" * 90)
    for e in entries:
        if e.get("asset_url"):
            status = "auto"
            size = _human(e.get("size_bytes_estimated"))
        else:
            status = "manual"
            size = "-"
        variant = e.get("variant", "primary")
        print(f"{e['body']:<10} {variant:<26} {e['agency']:<10} "
              f"{size:<10} {status}")


def cmd_cite(entries):
    """Print license + citation info for the filtered entries.

    Cite *both* the texture provider (the immediate source we redistribute
    via the catalogue) and the underlying mission/instrument when
    publishing figures."""
    notes = texture_license_notes()
    if notes:
        print("UMBRELLA LICENSE NOTES")
        print("-" * 22)
        import textwrap
        for line in textwrap.wrap(notes, width=78):
            print(line)
        print()
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


def cmd_fetch(entries, include_large: bool):
    download_dir = maps_dir()
    auto = [e for e in entries if e.get("asset_url")]
    manual = [e for e in entries if not e.get("asset_url")]

    skipped_large = []
    if not include_large:
        kept = []
        for e in auto:
            sz = e.get("size_bytes_estimated")
            if sz is not None and sz > LARGE_THRESHOLD:
                skipped_large.append(e)
            else:
                kept.append(e)
        auto = kept

    print(f"Downloading {len(auto)} map(s) to {download_dir}")
    download_dir.mkdir(parents=True, exist_ok=True)

    succeeded, failed = [], []
    for e in auto:
        fname = e.get("filename") or e["asset_url"].rsplit("/", 1)[-1]
        dest = download_dir / fname
        size_str = _human(e.get("size_bytes_estimated"))
        print(f"  {e['body']:<10} {e['agency']:<6} -> {fname} ({size_str})")
        if dest.exists():
            print(f"    skipping; already present "
                  f"({_human(dest.stat().st_size)})")
            succeeded.append((e, dest))
            continue
        try:
            download(e["asset_url"], dest)
            print(f"    ok ({_human(dest.stat().st_size)})")
            succeeded.append((e, dest))
            time.sleep(1.0)  # be polite to upstream
        except (urllib.error.URLError, urllib.error.HTTPError,
                TimeoutError) as exc:
            print(f"    FAILED: {exc}")
            failed.append((e, str(exc)))

    print()
    print(f"Downloaded: {len(succeeded)}   Failed: {len(failed)}   "
          f"Skipped (>{_human(LARGE_THRESHOLD)}): {len(skipped_large)}   "
          f"Manual-only: {len(manual)}")

    if skipped_large:
        print("\nSkipped large files (rerun with --include-large):")
        for e in skipped_large:
            print(f"  {e['body']:<10} {e['agency']:<6} "
                  f"{_human(e['size_bytes_estimated']):<10} {e['asset_url']}")

    if manual:
        print("\nManual-only entries (no direct asset URL). Visit the portal:")
        for e in manual:
            print(f"  {e['body']:<10} {e['agency']:<6} {e['mission']}")
            print(f"    {e['portal_url']}")
            if e.get("note"):
                print(f"    note: {e['note']}")

    if succeeded:
        print("\nSources used — please cite when publishing figures:")
        for e, _dest in succeeded:
            lic = e.get("license", "see registry")
            cite = e.get("citation") or e.get("provenance") or ""
            print(f"  {e['body']:<10} {e.get('variant', ''):<22} {lic}")
            if cite:
                print(f"             cite: {cite}")
        print("  (full block: implanet-fetch --cite  /  "
              "python -c 'import implanet; implanet.show_attribution()')")

    return 0 if not failed else 1


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="implanet-fetch", description=__doc__.splitlines()[0]
    )
    p.add_argument("--list", action="store_true",
                   help="Print manifest entries and exit (no download).")
    p.add_argument("--cite", action="store_true",
                   help="Print license + citation info for the matched "
                        "entries and exit (no download).")
    p.add_argument("--where", action="store_true",
                   help="Print the resolved maps directory and exit.")
    p.add_argument("--body", help="Filter by body name (e.g. Moon).")
    p.add_argument("--variant", help="Filter by variant key (e.g. sss_clouds).")
    p.add_argument("--agency", help="Filter by agency (NASA/ESA/JAXA/CNSA).")
    p.add_argument("--include-large", action="store_true",
                   help=f"Download files larger than {_human(LARGE_THRESHOLD)}.")
    p.add_argument("--manifest", default=None,
                   help="Path to an alternate manifest JSON (default: the "
                        "implanet.assets registry).")
    args = p.parse_args(argv)

    if args.where:
        print(maps_dir())
        return 0

    if args.manifest:
        with open(args.manifest) as f:
            entries = json.load(f)["maps"]
    else:
        entries = texture_entries()

    entries = _filter(entries, body=args.body, variant=args.variant,
                      agency=args.agency)
    if not entries:
        print("No entries matched.", file=sys.stderr)
        return 1

    if args.list:
        cmd_list(entries)
        return 0
    if args.cite:
        cmd_cite(entries)
        return 0
    return cmd_fetch(entries, args.include_large)


if __name__ == "__main__":
    raise SystemExit(main())
