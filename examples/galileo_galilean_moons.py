"""Galileo → the four Galilean moons, at their closest targeted
encounters. Reuses jup365.bsp (Galilean ephemerides, already present)
plus the Galileo reconstructed Jupiter-tour SPK.

Encounter times below are approximate; reproduce_flyby(refine_ca_hours=)
scans the SPK for the true closest-approach instant.
"""

from _flyby import reproduce_flyby, GLL_TOUR_SPK, JUP_SATELLITES_SPK

KERNELS = [GLL_TOUR_SPK, JUP_SATELLITES_SPK]


def main():
    # Ganymede G1 — first close flyby of the largest moon (~835 km).
    reproduce_flyby(
        utc="1996-06-27T06:29:00",
        body="Ganymede",
        body_radius_km=2631.2,
        spacecraft_naif_name="GALILEO ORBITER",
        spacecraft_label="Galileo (G1)",
        spk_origin="GANYMEDE",
        extra_kernels=KERNELS,
        texture_filename="ganymede_jonsson.jpg",
        output_filename="galileo_ganymede_G1.png",
        ambient=0.05,
        refine_ca_hours=2.0,
        note="G1 — first targeted Ganymede encounter",
    )

    # Callisto C10 (~539 km).
    reproduce_flyby(
        utc="1997-09-17T00:18:00",
        body="Callisto",
        body_radius_km=2410.3,
        spacecraft_naif_name="GALILEO ORBITER",
        spacecraft_label="Galileo (C10)",
        spk_origin="CALLISTO",
        extra_kernels=KERNELS,
        texture_filename="callisto_usgs_1k.jpg",
        output_filename="galileo_callisto_C10.png",
        ambient=0.05,
        refine_ca_hours=2.0,
        note="C10 encounter",
    )

    # Europa E12 — one of the closest Europa passes (~196 km).
    reproduce_flyby(
        utc="1997-12-16T12:03:00",
        body="Europa",
        body_radius_km=1560.8,
        spacecraft_naif_name="GALILEO ORBITER",
        spacecraft_label="Galileo (E12)",
        spk_origin="EUROPA",
        extra_kernels=KERNELS,
        texture_filename="europa_voyager_galileo_1k.jpg",
        output_filename="galileo_europa_E12.png",
        ambient=0.05,
        refine_ca_hours=2.0,
        note="E12 — low-altitude Europa pass",
    )

    # Io I27 — late-mission Io flyby over the active hemisphere (~198 km).
    reproduce_flyby(
        utc="2000-02-22T13:46:00",
        body="Io",
        body_radius_km=1821.6,
        spacecraft_naif_name="GALILEO ORBITER",
        spacecraft_label="Galileo (I27)",
        spk_origin="IO",
        extra_kernels=KERNELS,
        texture_filename="io_pia00319.jpg",
        output_filename="galileo_io_I27.png",
        ambient=0.05,
        refine_ca_hours=2.0,
        note="I27 — active-volcanism hemisphere",
    )


if __name__ == "__main__":
    main()
