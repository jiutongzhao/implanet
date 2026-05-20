"""Dawn → Mars gravity assist, closest approach 2009-02-18 00:28 UTC.

Dawn swung past Mars en route to Vesta/Ceres and took framing-camera
calibration images of the planet. (Closest approach verified by
scanning the reconstructed SPK: 549 km altitude at 2009-02-18
00:27:58 UTC.)
"""

from _flyby import reproduce_flyby, DAWN_MARS_SPK


def main():
    reproduce_flyby(
        utc="2009-02-18T00:27:58",
        body="Mars",
        body_radius_km=3389.5,
        spacecraft_naif_name="DAWN",
        spacecraft_label="Dawn",
        # de440s carries only MARS BARYCENTER (4), not Mars center (499);
        # Phobos/Deimos are negligible mass so the barycenter ≈ the
        # planet center to within meters.
        spk_origin="MARS BARYCENTER",
        extra_kernels=[DAWN_MARS_SPK],
        texture_filename="mars_sss_8k.jpg",
        output_filename="dawn_mars_2009-02-18T0028.png",
        ambient=0.05,
        note="Mars gravity assist (closest approach ~542 km altitude)",
    )


if __name__ == "__main__":
    main()
