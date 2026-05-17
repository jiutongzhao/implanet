"""Voyager 2 → Neptune (1989-08-25 03:56 UTC) and Triton (09:10 UTC).

The Neptune SPK ``vgr2_nep097.bsp`` covers the spacecraft trajectory
through both encounters; ``nep105.bsp`` adds Triton's body ephemeris
(needed because de440s only includes planet barycenters).
"""

from _flyby import reproduce_flyby, VGR2_NEP_SPK, NEP_SATELLITES_SPK


def main():
    reproduce_flyby(
        utc="1989-08-25T03:55:40",
        body="Neptune",
        body_radius_km=24622.0,
        spacecraft_naif_name="VOYAGER 2",
        spacecraft_label="Voyager 2",
        spk_origin="NEPTUNE BARYCENTER",
        extra_kernels=[VGR2_NEP_SPK, NEP_SATELLITES_SPK],
        texture_filename="neptune_sss.jpg",
        output_filename="voyager2_neptune_1989-08-25T0356.png",
        ambient=0.22,
        note="closest approach to Neptune (cloud-tops ~4,950 km)",
    )

    reproduce_flyby(
        utc="1989-08-25T09:10:00",
        body="Triton",
        body_radius_km=1353.4,
        spacecraft_naif_name="VOYAGER 2",
        spacecraft_label="Voyager 2",
        # nep105.bsp has Triton (801) center, so we can use it directly.
        spk_origin="TRITON",
        extra_kernels=[VGR2_NEP_SPK, NEP_SATELLITES_SPK],
        texture_filename="triton_voyager.jpg",
        output_filename="voyager2_triton_1989-08-25T0910.png",
        ambient=0.04,
        note="closest approach to Triton (~39,800 km from center)",
    )


if __name__ == "__main__":
    main()
