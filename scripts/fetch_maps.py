"""Download equirectangular planet maps listed in maps/manifest.json.

Entries with a non-null `asset_url` are downloaded automatically. Entries
with only a `portal_url` are reported as "manual" — the agency archive
requires a browser, login, or post-processing to obtain the map.

Usage
-----
    python scripts/fetch_maps.py                # download all auto entries
    python scripts/fetch_maps.py --list         # show every entry's status
    python scripts/fetch_maps.py --body Moon    # filter
    python scripts/fetch_maps.py --include-large  # allow files >200 MB
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "maps" / "manifest.json"
DOWNLOAD_DIR = REPO_ROOT / "maps" / "data"

LARGE_THRESHOLD = 200 * 1024 * 1024  # 200 MB


def _human(n: int | None) -> str:
    if n is None:
        return "unknown size"
    units = ["B", "KB", "MB", "GB"]
    s = float(n)
    for u in units:
        if s < 1024.0:
            return f"{s:.1f} {u}"
        s /= 1024.0
    return f"{s:.1f} TB"


def _download(url: str, dest: Path, retries: int = 4) -> int:
    """Download with retries on transient errors (429 / 5xx)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    headers = {
        "User-Agent": "implanet/0.1 (https://example.org/implanet; research)",
    }
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                read = 0
                chunk = 1 << 16
                last_pct = -1
                while True:
                    buf = r.read(chunk)
                    if not buf:
                        break
                    f.write(buf)
                    read += len(buf)
                    if total:
                        pct = int(100 * read / total)
                        if pct != last_pct and pct % 5 == 0:
                            print(f"    {pct:3d}% ({_human(read)} / {_human(total)})",
                                  end="\r")
                            last_pct = pct
                print(" " * 60, end="\r")
            tmp.replace(dest)
            return read
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < retries:
                wait = 5 * attempt
                print(f"    {exc.code}; retry {attempt}/{retries-1} in {wait}s")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < retries:
                wait = 3 * attempt
                print(f"    {exc}; retry {attempt}/{retries-1} in {wait}s")
                time.sleep(wait)
                continue
            raise


def _filter(entries, body=None, variant=None, agency=None):
    out = entries
    if body:
        out = [e for e in out if e["body"].lower() == body.lower()]
    if variant:
        out = [e for e in out if e.get("variant", "").lower() == variant.lower()]
    if agency:
        out = [e for e in out if e["agency"].lower() == agency.lower()]
    return out


def cmd_list(entries, args):
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


def cmd_fetch(entries, args):
    auto = [e for e in entries if e.get("asset_url")]
    manual = [e for e in entries if not e.get("asset_url")]

    skipped_large = []
    if not args.include_large:
        kept = []
        for e in auto:
            sz = e.get("size_bytes_estimated")
            if sz is not None and sz > LARGE_THRESHOLD:
                skipped_large.append(e)
            else:
                kept.append(e)
        auto = kept

    print(f"Downloading {len(auto)} map(s) to {DOWNLOAD_DIR}")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    succeeded, failed = [], []
    for e in auto:
        fname = e.get("filename") or e["asset_url"].rsplit("/", 1)[-1]
        dest = DOWNLOAD_DIR / fname
        size_str = _human(e.get("size_bytes_estimated"))
        print(f"  {e['body']:<10} {e['agency']:<6} -> {fname} ({size_str})")
        if dest.exists():
            print(f"    skipping; already present ({_human(dest.stat().st_size)})")
            succeeded.append((e, dest))
            continue
        try:
            n = _download(e["asset_url"], dest)
            print(f"    ok ({_human(n)})")
            succeeded.append((e, dest))
            time.sleep(1.0)  # be polite to upstream
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            print(f"    FAILED: {exc}")
            failed.append((e, str(exc)))

    print()
    print(f"Downloaded: {len(succeeded)}   Failed: {len(failed)}   "
          f"Skipped (>{_human(LARGE_THRESHOLD)}): {len(skipped_large)}   "
          f"Manual-only: {len(manual)}")

    if skipped_large:
        print("\nSkipped large files (rerun with --include-large):")
        for e in skipped_large:
            print(f"  {e['body']:<10} {e['agency']:<6} {_human(e['size_bytes_estimated']):<10} "
                  f"{e['asset_url']}")

    if manual:
        print("\nManual-only entries (no direct asset URL). Visit the portal:")
        for e in manual:
            print(f"  {e['body']:<10} {e['agency']:<6} {e['mission']}")
            print(f"    {e['portal_url']}")
            if e.get("note"):
                print(f"    note: {e['note']}")

    return 0 if not failed else 1


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--list", action="store_true",
                   help="Print manifest entries and exit (no download).")
    p.add_argument("--body", help="Filter by body name (e.g. Moon).")
    p.add_argument("--variant", help="Filter by variant key (e.g. sss_clouds).")
    p.add_argument("--agency", help="Filter by agency (NASA/ESA/JAXA/CNSA).")
    p.add_argument("--include-large", action="store_true",
                   help=f"Download files larger than {_human(LARGE_THRESHOLD)}.")
    p.add_argument("--manifest", default=str(MANIFEST),
                   help="Path to manifest JSON.")
    args = p.parse_args(argv)

    with open(args.manifest) as f:
        data = json.load(f)
    entries = _filter(data["maps"], body=args.body, variant=args.variant,
                       agency=args.agency)

    if not entries:
        print("No entries matched.", file=sys.stderr)
        return 1

    if args.list:
        cmd_list(entries, args)
        return 0
    return cmd_fetch(entries, args)


if __name__ == "__main__":
    raise SystemExit(main())
