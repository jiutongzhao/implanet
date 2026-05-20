"""MESSENGER → Venus, second flyby (V2), 2007-06-05 23:08 UTC.

Reuses the MESSENGER SPK from the Mercury-flyby example — its coverage
(2004-08-03 → 2008-02-16) includes the V2 Venus gravity assist.
"""

from _flyby import reproduce_flyby, MSGR_SPK


def main():
    reproduce_flyby(
        utc="2007-06-05T23:08:36",
        body="Venus",
        body_radius_km=6051.8,
        spacecraft_naif_name="MESSENGER",
        spacecraft_label="MESSENGER (V2)",
        extra_kernels=[MSGR_SPK],
        texture_filename="venus_sss_atmosphere_4k.jpg",
        output_filename="messenger_venus_2007-06-05T2308.png",
        ambient=0.30,        # cloud-top atmosphere, not a SAR mosaic
        note="second Venus flyby (closest approach ~338 km altitude)",
    )


if __name__ == "__main__":
    main()
