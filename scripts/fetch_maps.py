"""Dev shim — the implementation now lives in ``implanet.fetch`` so it
ships in the wheel and is exposed as the ``implanet-fetch`` console
command. Kept so existing docs / muscle memory still work:

    python scripts/fetch_maps.py [--list] [--body Moon] ...
"""

from implanet.fetch import main

if __name__ == "__main__":
    raise SystemExit(main())
