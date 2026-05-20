"""New Horizons → Pluto (2015-07-14 11:49 UTC) and Charon (12:03 UTC).

The single SPK ``nh_plu047_od122.bsp`` contains both the spacecraft
trajectory AND the Pluto-system body ephemerides (Pluto, Charon, Nix,
Hydra, Kerberos, Styx). For Pluto/Charon we must use the body center
as origin, not the system barycenter: with Charon at ~12% of Pluto's
mass, the Pluto-Charon barycenter sits ~2,100 km *outside* Pluto's
surface, which at NH's CA distance of 12,500 km is a 16% error.
"""

from _flyby import reproduce_flyby, NH_PLUTO_SPK


def main():
    reproduce_flyby(
        utc="2015-07-14T11:49:57",
        body="Pluto",
        body_radius_km=1188.3,
        spacecraft_naif_name="NEW HORIZONS",
        spacecraft_label="New Horizons",
        spk_origin="PLUTO",     # use Pluto center (id 999), NOT barycenter
        extra_kernels=[NH_PLUTO_SPK],
        texture_filename="pluto_new_horizons_600m.jpg",
        output_filename="new_horizons_pluto_2015-07-14T1149.png",
        ambient=0.03,
        note="closest approach (~12,500 km from Pluto center)",
    )

    reproduce_flyby(
        utc="2015-07-14T12:03:50",
        body="Charon",
        body_radius_km=606.0,
        spacecraft_naif_name="NEW HORIZONS",
        spacecraft_label="New Horizons",
        spk_origin="CHARON",
        extra_kernels=[NH_PLUTO_SPK],
        texture_filename="charon_new_horizons.jpg",
        output_filename="new_horizons_charon_2015-07-14T1203.png",
        ambient=0.03,
        note="closest approach to Charon (~28,800 km)",
    )


if __name__ == "__main__":
    main()
