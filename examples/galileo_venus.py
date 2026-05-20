"""Galileo → Venus, the only Galileo Venus flyby, 1990-02-10.

Galileo used Venus for a gravity assist on its VEEGA route to Jupiter,
imaging the cloud tops in violet/near-IR. Uses the Galileo cruise SPK.
"""

from _flyby import reproduce_flyby, GLL_CRUISE_SPK


def main():
    reproduce_flyby(
        utc="1990-02-10T05:58:00",
        body="Venus",
        body_radius_km=6051.8,
        spacecraft_naif_name="GALILEO ORBITER",
        spacecraft_label="Galileo",
        extra_kernels=[GLL_CRUISE_SPK],
        texture_filename="venus_sss_atmosphere_4k.jpg",
        output_filename="galileo_venus_1990-02-10.png",
        ambient=0.30,
        refine_ca_hours=3.0,
        note="VEEGA Venus gravity assist (~16,100 km closest approach)",
    )


if __name__ == "__main__":
    main()
