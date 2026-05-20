"""Voyager 1 → Jupiter, closest approach 1979-03-05 12:05 UTC."""

from _flyby import reproduce_flyby, VGR1_JUP_SPK


def main():
    reproduce_flyby(
        utc="1979-03-05T12:05:26",
        body="Jupiter",
        body_radius_km=69911.0,
        spacecraft_naif_name="VOYAGER 1",
        spacecraft_label="Voyager 1",
        # Jupiter barycenter is fine — Voyager 1 at CA was ~349,000 km
        # from Jupiter center; barycenter offset (driven by Galilean moons)
        # is ~kilometers, negligible at this scale.
        spk_origin="JUPITER BARYCENTER",
        extra_kernels=[VGR1_JUP_SPK],
        texture_filename="jupiter_cassini_pia07782.jpg",
        output_filename="voyager1_jupiter_1979-03-05T1205.png",
        ambient=0.15,
        note="closest approach (cloud-tops ~280,000 km)",
    )


if __name__ == "__main__":
    main()
