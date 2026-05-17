"""Load the texture (manifest.json) and kernel (kernels.json) registries.

Resolution order per file (first match wins):

  1. ``$IMPLANET_REGISTRY/<name>``     (explicit override dir)
  2. ``<repo>/maps/<name>``            (authoritative in a dev checkout)
  3. packaged copy in ``implanet/assets/data/<name>`` (pip install)

The packaged copies are refreshed from the repo files by
``scripts/sync_registry.py``; ``tests/test_assets.py`` asserts they
stay byte-identical so the two never silently diverge.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from implanet.assets._cache import _find_repo_root

_MANIFEST = "manifest.json"
_KERNELS = "kernels.json"
_PACKAGED = Path(__file__).resolve().parent / "data"


def _resolve(name: str) -> Path:
    env = os.environ.get("IMPLANET_REGISTRY")
    if env:
        p = Path(env) / name
        if p.is_file():
            return p
    repo = _find_repo_root()
    if repo is not None:
        p = repo / "maps" / name
        if p.is_file():
            return p
    p = _PACKAGED / name
    if p.is_file():
        return p
    raise FileNotFoundError(
        f"Could not locate registry {name!r}. Set IMPLANET_REGISTRY to a "
        f"directory containing it, or reinstall the package."
    )


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    with open(_resolve(name), encoding="utf-8") as f:
        return json.load(f)


def texture_registry() -> dict:
    """Full parsed manifest.json (keys: schema_version, ..., maps)."""
    return _load(_MANIFEST)


def kernel_registry() -> dict:
    """Full parsed kernels.json (keys: schema_version, ..., kernels)."""
    return _load(_KERNELS)


def texture_entries() -> list:
    return texture_registry()["maps"]


def kernel_entries() -> list:
    return kernel_registry()["kernels"]


def find_texture(body: str, variant: Optional[str] = None) -> dict:
    """Return the manifest entry for a body (+ optional variant).

    With no variant, returns the first entry for that body that has a
    direct ``asset_url`` (auto-downloadable), else the first entry.
    """
    body_l = body.lower()
    matches = [e for e in texture_entries() if e["body"].lower() == body_l]
    if not matches:
        raise KeyError(f"No texture for body {body!r} in manifest.json")
    if variant is not None:
        for e in matches:
            if e.get("variant", "").lower() == variant.lower():
                return e
        raise KeyError(
            f"No texture for {body!r} variant {variant!r}. Available: "
            f"{[e.get('variant') for e in matches]}"
        )
    for e in matches:
        if e.get("asset_url"):
            return e
    return matches[0]


def find_kernel(key: str) -> dict:
    """Return the kernels.json entry by `id` or by exact `filename`."""
    for e in kernel_entries():
        if e["id"] == key or e["filename"] == key:
            return e
    raise KeyError(
        f"No kernel {key!r} in kernels.json. Known ids: "
        f"{[e['id'] for e in kernel_entries()]}"
    )
