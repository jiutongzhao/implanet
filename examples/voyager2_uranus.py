"""Voyager 2 → Uranus, closest approach 1986-01-24 17:58 UTC."""

from _flyby import reproduce_flyby, VGR2_URA_SPK


def main():
    reproduce_flyby(
        utc="1986-01-24T17:58:51",
        body="Uranus",
        body_radius_km=25362.0,
        spacecraft_naif_name="VOYAGER 2",
        spacecraft_label="Voyager 2",
        spk_origin="URANUS BARYCENTER",  # Uranian moons → barycenter offset ~tens of km
        extra_kernels=[VGR2_URA_SPK],
        texture_filename="uranus_sss.jpg",
        output_filename="voyager2_uranus_1986-01-24T1758.png",
        ambient=0.20,
        note="closest approach (81,500 km from cloud tops, pole-on geometry)",
    )


if __name__ == "__main__":
    main()
