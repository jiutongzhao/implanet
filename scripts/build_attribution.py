"""Regenerate ATTRIBUTION.md from the texture + kernel registries.

The file at the repo root is the human-browseable copy (rendered on
GitHub / PyPI). The same data is reachable at runtime via
``implanet.show_attribution()`` / ``implanet-fetch --cite``; this script
just freezes it into a Markdown file so it shows up before install.

Run after editing ``maps/manifest.json`` or ``maps/kernels.json``;
``scripts/sync_registry.py`` calls this automatically.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "maps" / "manifest.json"
KERNELS = REPO / "maps" / "kernels.json"
OUT = REPO / "ATTRIBUTION.md"

PREAMBLE = """\
# Attribution & citation

`implanet` itself is MIT-licensed (see `LICENSE`). The **maps and SPICE
kernels** it downloads on demand are **not** owned by this project —
they're redistributions of public-domain or Creative-Commons assets from
NASA, ESA, JAXA, CNSA, USGS, and a few community texture providers.

**If you use any rendered figure in a publication or talk, you must
credit the original mission/instrument *and* the texture provider.**
The per-entry blocks below give the exact citation phrasing for each
map; reproduce or paraphrase that text in your figure caption or
acknowledgements.

You can also read this information at runtime, so it stays in sync with
the catalogue:

```python
import implanet
implanet.show_attribution("Mars")     # one body
implanet.show_attribution()           # everything
implanet.attribution("Earth", "natural_earth3")   # → dict
```

```bash
implanet-fetch --cite                 # citation block from the CLI
implanet-fetch --cite --body Mars     # filtered
```

`implanet.get_texture(body)` also prints a one-line license + cite hint
to stderr the *first time* it downloads a given texture, so the
attribution requirement is hard to miss.

---

"""


def _block(entry: dict, header_prefix: str = "") -> str:
    body = entry.get("body", "?")
    variant = entry.get("variant", "")
    title = f"{body} / {variant}" if variant else body
    lines = [f"### {header_prefix}{title}", ""]
    for key in ("agency", "mission", "instrument", "description",
                "provenance", "license", "citation", "portal_url",
                "asset_url", "note"):
        v = entry.get(key)
        if v:
            lines.append(f"- **{key}**: {v}")
    lines.append("")
    return "\n".join(lines)


def _kernel_block(entry: dict) -> str:
    lines = [f"### {entry['id']}  ({entry['filename']})", ""]
    for key in ("category", "description", "provenance", "license",
                "url"):
        v = entry.get(key)
        if v:
            lines.append(f"- **{key}**: {v}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not MANIFEST.is_file():
        print(f"  ! missing {MANIFEST}", file=sys.stderr)
        return 1
    if not KERNELS.is_file():
        print(f"  ! missing {KERNELS}", file=sys.stderr)
        return 1

    tex = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ker = json.loads(KERNELS.read_text(encoding="utf-8"))

    out = [PREAMBLE]

    out.append("## Umbrella license notes\n")
    out.append("**Textures.** " + tex.get("license_notes", "") + "\n")
    out.append("**SPICE kernels.** " + ker.get("license_notes", "") + "\n")
    out.append("\n---\n")

    out.append("## Texture maps\n")
    for e in tex["maps"]:
        out.append(_block(e))

    out.append("---\n")
    out.append("## SPICE kernels\n")
    for e in ker["kernels"]:
        out.append(_kernel_block(e))

    OUT.write_text("\n".join(out), encoding="utf-8")
    try:
        shown = OUT.relative_to(REPO)
    except ValueError:
        shown = OUT
    print(f"  wrote {shown} "
          f"({len(tex['maps'])} textures + {len(ker['kernels'])} kernels)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
