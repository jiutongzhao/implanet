"""Voyager 2 → Saturn, closest approach 1981-08-26 03:24 UTC."""

from _flyby import reproduce_flyby, VGR2_SAT_SPK


def main():
    reproduce_flyby(
        utc="1981-08-26T03:24:05",
        body="Saturn",
        body_radius_km=58232.0,
        spacecraft_naif_name="VOYAGER 2",
        spacecraft_label="Voyager 2",
        spk_origin="SATURN BARYCENTER",
        extra_kernels=[VGR2_SAT_SPK],
        texture_filename="saturn_sss.jpg",
        output_filename="voyager2_saturn_1981-08-26T0324.png",
        ambient=0.20,
        note="closest approach (~101,000 km from cloud tops)",
    )


if __name__ == "__main__":
    main()
