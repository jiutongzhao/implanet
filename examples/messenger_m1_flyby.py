"""MESSENGER M1 (first Mercury flyby), 2008-01-14 20:24 UTC."""

from _flyby import reproduce_flyby, MSGR_SPK


def main():
    reproduce_flyby(
        utc="2008-01-14T20:24:00",
        body="Mercury",
        body_radius_km=2439.7,
        spacecraft_naif_name="MESSENGER",
        spacecraft_label="MESSENGER (M1)",
        extra_kernels=[MSGR_SPK],
        texture_filename="mercury_messenger_enhanced_color_32ppd.jpg",
        output_filename="messenger_m1_2008-01-14T2024.png",
        grayscale=True,        # MDIS captured this as single-band frames
        ambient=0.04,
        note="MDIS B&W approximation",
    )


if __name__ == "__main__":
    main()
