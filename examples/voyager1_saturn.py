"""Voyager 1 → Saturn, closest approach 1980-11-12 23:46 UTC."""

from _flyby import reproduce_flyby, VGR1_SAT_SPK


def main():
    reproduce_flyby(
        utc="1980-11-12T23:46:30",
        body="Saturn",
        body_radius_km=58232.0,
        spacecraft_naif_name="VOYAGER 1",
        spacecraft_label="Voyager 1",
        spk_origin="SATURN BARYCENTER",
        extra_kernels=[VGR1_SAT_SPK],
        texture_filename="saturn_sss.jpg",
        output_filename="voyager1_saturn_1980-11-12T2346.png",
        ambient=0.20,
        note="closest approach (~124,000 km from cloud tops)",
    )


if __name__ == "__main__":
    main()
