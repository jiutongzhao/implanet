"""Voyager 1 → Io, closest approach 1979-03-05 15:14 UTC.

Reuses the Voyager 1 Jupiter SPK already downloaded for the Jupiter
flyby; adds jup348.bsp for Io's body ephemeris (de440s has no moons).
This is the encounter that revealed Io's active volcanism.
"""

from _flyby import reproduce_flyby, VGR1_JUP_SPK, JUP_SATELLITES_SPK


def main():
    reproduce_flyby(
        utc="1979-03-05T15:14:00",
        body="Io",
        body_radius_km=1821.6,
        spacecraft_naif_name="VOYAGER 1",
        spacecraft_label="Voyager 1",
        spk_origin="IO",      # jup348.bsp carries Io (501) center
        extra_kernels=[VGR1_JUP_SPK, JUP_SATELLITES_SPK],
        texture_filename="io_pia00319.jpg",
        output_filename="voyager1_io_1979-03-05T1514.png",
        ambient=0.05,
        note="closest approach to Io (~20,570 km) — active volcanism discovery",
    )


if __name__ == "__main__":
    main()
