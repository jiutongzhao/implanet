"""Cache-directory resolution and a shared, resumable-ish downloader.

Resolution order for the cache roots (first match wins):

Kernels:
  1. ``$IMPLANET_KERNELS``                 (explicit dir; back-compat)
  2. ``$IMPLANET_CACHE/kernels``
  3. ``<repo>/kernels``                    (in-repo dev checkout)
  4. ``<site-packages>/implanet/_data/kernels``  (pip default)
  5. ``<user-cache>/implanet/kernels``     (only if 4 is read-only)

Maps/textures: same shape, with ``_data/maps`` / ``maps``.

The pip-installed default keeps assets *with the package*
(``site-packages/implanet/_data``). If that directory isn't writable
(system-managed Python, read-only install), it transparently falls back
to the user cache so downloads never hard-fail. ``<user-cache>`` is
``$XDG_CACHE_HOME`` if set, else ``~/.cache`` (``~/Library/Caches`` on
macOS, ``%LOCALAPPDATA%`` on Windows).
"""

from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Optional


def _user_cache_base() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches"
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            return Path(local)
    return Path.home() / ".cache"


def _find_repo_root() -> Optional[Path]:
    """Walk up from this file and cwd looking for the repo's maps/manifest.json."""
    candidates = [Path(__file__).resolve(), Path.cwd().resolve()]
    for start in candidates:
        for parent in [start, *start.parents]:
            if (parent / "maps" / "manifest.json").is_file():
                return parent
    return None


def _package_base() -> Path:
    """``site-packages/implanet/_data`` (this file is implanet/assets/_cache.py)."""
    return Path(__file__).resolve().parent.parent / "_data"


@lru_cache(maxsize=1)
def _default_base() -> Path:
    """Default asset root when no env override and not a dev checkout.

    Keep assets *with the package* (the user's stated preference). Probe
    the package dir for writability once; if it's read-only (system
    Python, managed install), fall back to the user cache so downloads
    never hard-fail. Cached so the probe runs at most once per process.
    """
    pkg = _package_base()
    try:
        pkg.mkdir(parents=True, exist_ok=True)
        probe = pkg / ".write_test"
        probe.write_text("")
        probe.unlink()
        return pkg
    except OSError:
        return _user_cache_base() / "implanet"


def cache_base() -> Path:
    """Root under which the implanet user cache lives."""
    explicit = os.environ.get("IMPLANET_CACHE")
    if explicit:
        return Path(explicit)
    return _user_cache_base() / "implanet"


def kernels_dir() -> Path:
    env = os.environ.get("IMPLANET_KERNELS")
    if env:
        return Path(env)
    if os.environ.get("IMPLANET_CACHE"):
        return cache_base() / "kernels"
    repo = _find_repo_root()
    if repo is not None and (repo / "kernels").is_dir():
        return repo / "kernels"
    return _default_base() / "kernels"


def maps_dir() -> Path:
    env = os.environ.get("IMPLANET_MAPS")
    if env:
        return Path(env)
    if os.environ.get("IMPLANET_CACHE"):
        return cache_base() / "maps"
    repo = _find_repo_root()
    if repo is not None and (repo / "maps" / "data").is_dir():
        return repo / "maps" / "data"
    return _default_base() / "maps"


def _human(n: Optional[int]) -> str:
    if not n:
        return "unknown size"
    s = float(n)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if s < 1024.0:
            return f"{s:.1f} {u}"
        s /= 1024.0
    return f"{s:.1f} PB"


def download(url: str, dest: Path, *, expected_size: Optional[int] = None,
             retries: int = 4, timeout: int = 120,
             quiet: bool = False) -> Path:
    """Download `url` to `dest` atomically; return `dest`.

    Skips the download if `dest` already exists and (when known) matches
    `expected_size`. Writes to a ``.part`` sidecar and renames on
    success so an interrupted download never leaves a half file in place.
    """
    if dest.exists():
        if expected_size is None or dest.stat().st_size == expected_size:
            return dest
        # Size mismatch — re-fetch.
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    headers = {"User-Agent": "implanet (research; +https://pypi.org/project/implanet)"}

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                read = 0
                last_pct = -1
                while True:
                    buf = r.read(1 << 16)
                    if not buf:
                        break
                    f.write(buf)
                    read += len(buf)
                    if not quiet and total:
                        pct = int(100 * read / total)
                        if pct != last_pct and pct % 5 == 0:
                            print(f"    {pct:3d}%  ({_human(read)} / "
                                  f"{_human(total)})", end="\r")
                            last_pct = pct
                if not quiet and total:
                    print(" " * 64, end="\r")
            tmp.replace(dest)
            return dest
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503) and attempt < retries:
                wait = 5 * attempt
                if not quiet:
                    print(f"    HTTP {exc.code}; retry {attempt}/{retries-1} "
                          f"in {wait}s")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < retries:
                wait = 3 * attempt
                if not quiet:
                    print(f"    {exc}; retry {attempt}/{retries-1} in {wait}s")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"unreachable: download retry loop exited for {url}")
