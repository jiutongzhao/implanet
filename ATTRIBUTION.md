# Attribution & citation

`implanet` itself is MIT-licensed (see `LICENSE`). The **maps and SPICE
kernels** it downloads on demand are **not** owned by this project —
they're redistributions of public-domain or Creative-Commons assets from
NASA, ESA, JAXA, CNSA, USGS, and a few community texture providers.

**If you use any rendered figure in a publication or talk, you must
credit the original mission/instrument *and* the texture provider.**
The per-entry blocks below give the exact citation phrasing for each
map; reproduce or paraphrase that text in your figure caption or
acknowledgements.

You can also read this information at runtime, so it stays in sync with
the catalogue:

```python
import implanet
implanet.show_attribution("Mars")     # one body
implanet.show_attribution()           # everything
implanet.attribution("Earth", "natural_earth3")   # → dict
```

```bash
implanet-fetch --cite                 # citation block from the CLI
implanet-fetch --cite --body Mars     # filtered
```

`implanet.get_texture(body)` also prints a one-line license + cite hint
to stderr the *first time* it downloads a given texture, so the
attribution requirement is hard to miss.

---


## Umbrella license notes

**Textures.** NASA imagery is public domain unless otherwise stated. ESA images are generally CC BY-SA 3.0 IGO. JAXA SELENE/Kaguya data carry JAXA-specific terms — see https://www.kaguya.jaxa.jp/en/ for use conditions. CNSA Chang'e data is distributed via NAOC public release terms. Textures sourced from Solar System Scope (via Wikimedia) are CC BY 4.0 by INOVE s.r.o., based on the cited agency data.

**SPICE kernels.** NAIF/JPL SPICE kernels are produced by NASA and are in the public domain unless noted. The generic planetary ephemeris (DE440s), leapseconds (LSK) and planetary constants (PCK) are NAIF generic kernels. Mission trajectory SPKs come from each mission's PDS SPICE archive. Always cite the producing mission/NAIF in published work.


---

## Texture maps

### Sun / sss

- **agency**: NASA / ESA
- **mission**: SDO / SOHO photospheric composites (Solar System Scope processing)
- **instrument**: Multi-instrument composite
- **description**: Quiet-photosphere visual texture for rendering. Not a science map.
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying solar imagery NASA SDO / ESA-NASA SOHO
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA SDO / ESA-NASA SOHO photospheric imagery.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_sun.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/a/a4/Solarsystemscope_texture_8k_sun.jpg
- **note**: The Sun has no meaningful sub-solar geometry; render with ambient=1.0.

### Mercury / messenger_bdr_mono

- **agency**: NASA
- **mission**: MESSENGER
- **instrument**: MDIS (WAC/NAC 750 nm)
- **description**: MESSENGER MDIS Best Direct Resolution (BDR) global monochrome basemap at 166 m/pixel (32 pixels per degree). Single-band reflectance from WAC 750 nm and NAC monochrome frames; the standard B&W albedo product.
- **provenance**: Wikimedia Commons (USGS Astrogeology)
- **license**: Public Domain (NASA/JHU-APL/USGS)
- **citation**: USGS Astrogeology; MESSENGER MDIS team, NASA/JHU-APL. BDR (Best Direct Resolution) global monochrome basemap at 166 m/pixel, MDIS WAC/NAC 750 nm imaging.
- **portal_url**: https://astrogeology.usgs.gov/search/map/Mercury/Messenger/Global/Mercury_MESSENGER_MDIS_Basemap_BDR_Mosaic_Global_166m
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/c/c8/Mercury_MESSENGER_MDIS_Basemap_BDR_Mosaic_Global_32ppd.jpg

### Mercury / messenger_enhanced_color

- **agency**: NASA
- **mission**: MESSENGER
- **instrument**: MDIS (3-band statistical stretch)
- **description**: MESSENGER MDIS Enhanced Color global mosaic at 665 m/pixel (32 pixels per degree). Pseudo-color from a 3-band statistical stretch revealing compositional variation across Mercury’s surface.
- **provenance**: Wikimedia Commons (USGS Astrogeology)
- **license**: Public Domain (NASA/JHU-APL/USGS)
- **citation**: Denevi, B. W. et al., USGS Astrogeology; MESSENGER MDIS team, NASA/JHU-APL. Enhanced color mosaic constructed from MDIS WAC filters 996/748/430 nm in PCA stretch.
- **portal_url**: https://astrogeology.usgs.gov/search/map/Mercury/Messenger/Global/Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_665m
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/4/41/Mercury_MESSENGER_MDIS_Basemap_EnhancedColor_Mosaic_Global_32ppd.jpg

### Mercury / sss

- **agency**: NASA
- **mission**: MESSENGER
- **instrument**: Mercury Dual Imaging System (MDIS)
- **description**: Color-enhanced MDIS global mosaic, processed by Solar System Scope from MESSENGER data
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying MESSENGER imagery is public domain (NASA/JHU-APL)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: Hawkins, S. E., et al. MESSENGER/MDIS team, NASA/JHU-APL.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_mercury.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/2/27/Solarsystemscope_texture_8k_mercury.jpg

### Mercury / messenger_basemap_fullres

- **agency**: NASA
- **mission**: MESSENGER
- **instrument**: MDIS
- **description**: Full-resolution USGS MESSENGER MDIS basemap, accessible via Astropedia portal
- **provenance**: USGS Astrogeology Science Center
- **license**: Public Domain (NASA/USGS)
- **citation**: USGS Astrogeology MESSENGER/MDIS basemap, v2.
- **portal_url**: https://astrogeology.usgs.gov/search?pmi-target=MERCURY
- **note**: Direct asset URL is unstable. Download manually from the Astropedia portal.

### Venus / sss_atmosphere

- **agency**: NASA / ESA / JAXA
- **mission**: Pioneer Venus / Venus Express / Akatsuki (composite)
- **instrument**: UV cloud-top imaging (composite)
- **description**: Cloud-top UV map of Venus's atmosphere
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying UV imagery NASA / ESA / JAXA
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: Pioneer Venus / Venus Express / Akatsuki UV imaging.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_4k_venus_atmosphere.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/5/57/Solarsystemscope_texture_4k_venus_atmosphere.jpg

### Venus / sss_surface

- **agency**: NASA
- **mission**: Magellan
- **instrument**: Synthetic Aperture Radar (SAR)
- **description**: Magellan SAR global mosaic, processed by Solar System Scope
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying Magellan imagery is public domain (NASA/JPL)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA Magellan Project; USGS Astrogeology.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_venus_surface.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/1/1c/Solarsystemscope_texture_8k_venus_surface.jpg

### Earth / blue_marble

- **agency**: NASA
- **mission**: MODIS / Blue Marble Next Generation
- **instrument**: MODIS (Terra/Aqua)
- **description**: Cloud-free monthly composite, August 2004, with topography and bathymetry
- **license**: Public Domain (NASA)
- **citation**: Reto Stockli, NASA Earth Observatory / Blue Marble Next Generation, 2005.
- **portal_url**: https://visibleearth.nasa.gov/collection/1484/blue-marble
- **asset_url**: https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg

### Earth / blue_marble_8k

- **agency**: NASA
- **mission**: MODIS / Blue Marble Next Generation
- **instrument**: MODIS (Terra/Aqua)
- **description**: Cloud-free composite without bathymetry, 8192-wide TIFF
- **license**: Public Domain (NASA)
- **citation**: Reto Stockli, NASA Earth Observatory, Blue Marble Next Generation.
- **portal_url**: https://visibleearth.nasa.gov/images/57752/blue-marble-land-surface-shallow-water-and-shaded-topography
- **asset_url**: https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57752/land_shallow_topo_8192.tif

### Earth / sss_clouds

- **agency**: NASA
- **mission**: Earth cloud composite (Solar System Scope processing)
- **instrument**: MODIS / GOES composites
- **description**: Equirectangular cloud-cover albedo map, 8K
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying cloud imagery is public domain (NASA)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA Earth Observatory cloud composites.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_earth_clouds.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/7/7a/Solarsystemscope_texture_8k_earth_clouds.jpg

### Earth / sss_daymap

- **agency**: NASA
- **mission**: MODIS Blue Marble (Solar System Scope processing)
- **instrument**: MODIS
- **description**: SSS day-side Earth texture, 8K, smoothed for rendering
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying MODIS Blue Marble is public domain (NASA)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA MODIS Blue Marble.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_earth_daymap.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/0/04/Solarsystemscope_texture_8k_earth_daymap.jpg

### Earth / sss_nightmap

- **agency**: NASA
- **mission**: NASA Earth at Night (Solar System Scope processing)
- **instrument**: Suomi-NPP VIIRS Day/Night Band
- **description**: City lights / night-side Earth, 8K
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying VIIRS imagery is public domain (NASA/NOAA)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA Earth at Night / Suomi-NPP VIIRS.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_earth_nightmap.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/b/b3/Solarsystemscope_texture_8k_earth_nightmap.jpg

### Earth / natural_earth3

- **agency**: Natural Earth
- **mission**: Natural Earth III (Tom Patterson)
- **instrument**: Cartographic raster (hand-tuned colour)
- **description**: Vivid stylised land/ocean colouring, no ice or clouds — brighter and more saturated than the photographic Blue Marble
- **license**: Public Domain (Natural Earth / Tom Patterson)
- **citation**: Tom Patterson, Natural Earth III, www.shadedrelief.com/natural3, public domain.
- **portal_url**: https://www.shadedrelief.com/natural3/pages/textures.html
- **asset_url**: https://www.shadedrelief.com/natural3/ne3_data/8192/textures/3_no_ice_clouds_8k.jpg

### Moon / clementine_uvvis

- **agency**: NASA / USAF
- **mission**: Clementine
- **instrument**: UVVIS camera
- **description**: Clementine 750 nm albedo simple-cylindrical mosaic, low-res
- **provenance**: Wikimedia Commons (NASA / USGS)
- **license**: Public Domain (NASA/DoD)
- **citation**: Clementine mission (1994) UVVIS team; USGS Astrogeology.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Clementine_albedo_simp750.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/e/ea/Clementine_albedo_simp750.jpg

### Moon / lroc_color_2019

- **agency**: NASA
- **mission**: Lunar Reconnaissance Orbiter (LRO)
- **instrument**: LROC Wide Angle Camera
- **description**: Global color albedo map (2019 release), 4K equirectangular
- **license**: Public Domain (NASA)
- **citation**: Ernie Wright, NASA Goddard SVS; LRO LROC WAC color mosaic.
- **portal_url**: https://svs.gsfc.nasa.gov/4720
- **asset_url**: https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_poles_4k.tif

### Moon / lroc_color_2025

- **agency**: NASA
- **mission**: Lunar Reconnaissance Orbiter (LRO)
- **instrument**: LROC Wide Angle Camera
- **description**: Global color albedo map (2025 release), 4K equirectangular
- **license**: Public Domain (NASA)
- **citation**: NASA Goddard SVS / LRO LROC team; based on >100,000 LROC WAC images.
- **portal_url**: https://svs.gsfc.nasa.gov/4720
- **asset_url**: https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_16bit_srgb_4k.tif

### Moon / sss

- **agency**: NASA
- **mission**: LRO LROC (Solar System Scope processing)
- **instrument**: LROC WAC
- **description**: SSS lunar grayscale 8K texture
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying LROC data is public domain (NASA)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA LRO LROC team.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_moon.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/d/d1/Solarsystemscope_texture_8k_moon.jpg

### Moon / change2

- **agency**: CNSA
- **mission**: Chang'e-2
- **instrument**: CCD Stereo Camera
- **description**: Chang'e-2 global lunar mosaic at 7 m/pixel
- **license**: CNSA / NAOC public release terms — see portal
- **citation**: Chinese National Space Administration (CNSA) / National Astronomical Observatories of China (NAOC).
- **portal_url**: https://moon.bao.ac.cn/
- **note**: Requires registration on the Lunar and Planetary Data Release System (LPDR).

### Moon / kaguya_tc

- **agency**: JAXA
- **mission**: SELENE (Kaguya)
- **instrument**: Terrain Camera (TC)
- **description**: Kaguya TC ortho-mosaic and DEM products (multi-resolution)
- **license**: JAXA SELENE data use conditions — see portal
- **citation**: JAXA, SELENE (Kaguya) project, Terrain Camera team.
- **portal_url**: https://darts.isas.jaxa.jp/planet/pdap/selene/
- **note**: Requires JAXA DARTS / SELENE Data Archive registration in some cases.

### Mars / sss

- **agency**: NASA
- **mission**: MGS MOLA + Viking
- **instrument**: MOLA topography colored, Viking visual
- **description**: Mars global color/topography composite processed by Solar System Scope
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying MOLA/Viking imagery is public domain (NASA)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA MGS MOLA team; Viking Orbiter; USGS Astrogeology.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_mars.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/7/70/Solarsystemscope_texture_8k_mars.jpg

### Mars / viking_mdim21_1km

- **agency**: NASA
- **mission**: Viking Orbiters
- **instrument**: Viking VIS imaging
- **description**: USGS Viking MDIM 2.1 color mosaic, 1 km/pixel — original Viking-only processing
- **provenance**: Wikimedia Commons (USGS Astrogeology)
- **license**: Public Domain (NASA/USGS)
- **citation**: USGS Astrogeology, Mars Viking MDIM 2.1 color mosaic (1 km/pixel). Underlying data: NASA Viking Orbiter (1976-80).
- **portal_url**: https://commons.wikimedia.org/wiki/File:Mars_Viking_MDIM21_ClrMosaic_1km.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/1/1f/Mars_Viking_MDIM21_ClrMosaic_1km.jpg

### Mars / viking_mdim21_fullres

- **agency**: NASA
- **mission**: Viking Orbiters
- **instrument**: Viking visual imaging
- **description**: Full-resolution USGS MDIM 2.1 global color mosaic at 232 m/pixel
- **provenance**: USGS Astrogeology Science Center
- **license**: Public Domain (NASA/USGS)
- **citation**: USGS Astrogeology MDIM 2.1, based on Viking Orbiter imagery (1976-80).
- **portal_url**: https://astrogeology.usgs.gov/search/map/Mars/Viking/MDIM21/Mars_Viking_MDIM21_ClrMosaic_global_232m
- **asset_url**: https://planetarymaps.usgs.gov/mosaic/Mars_Viking_MDIM21_ClrMosaic_global_232m.tif
- **note**: 12.7 GB. Disabled by default in fetch script; pass --include-large to download.

### Mars / mars_express_hrsc

- **agency**: ESA
- **mission**: Mars Express
- **instrument**: HRSC (High Resolution Stereo Camera)
- **description**: HRSC global color mosaic at 50 m/pixel, distributed by DLR/FU Berlin
- **license**: ESA / DLR / FU Berlin, CC BY-SA 3.0 IGO
- **citation**: Gwinner, K., et al. (2016) Planetary and Space Science 126, 93-138.
- **portal_url**: https://maps.planet.fu-berlin.de/
- **note**: Distributed as tiled GeoTIFFs through the FU Berlin map server; no single-file equirectangular download. Manual stitching required.

### Mars / tianwen1

- **agency**: CNSA
- **mission**: Tianwen-1
- **instrument**: Moderate Resolution Imaging Camera (MoRIC)
- **description**: Tianwen-1 global Mars color mosaic released by CNSA in 2023
- **license**: CNSA / NAOC public release terms
- **citation**: Tianwen-1 mission team, CNSA / NAOC, 2023.
- **portal_url**: https://moon.bao.ac.cn/
- **note**: Distributed through the LPDR Mars data portal; registration required.

### Phobos / dlr_viking_hrsc

- **agency**: NASA / ESA
- **mission**: Viking Orbiter + Mars Express
- **instrument**: Viking VIS / HRSC
- **description**: Phobos global mosaic controlled by DLR using Viking and Mars Express HRSC
- **provenance**: Wikimedia Commons / DLR (Deutsches Zentrum für Luft- und Raumfahrt)
- **license**: Public Domain (NASA Viking imagery) / DLR processing
- **citation**: DLR Phobos mosaic, controlled with Viking Orbiter and ESA Mars Express HRSC.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Phobos_Viking_Mosaic_DLRcontrol_7200.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/a/a9/Phobos_Viking_Mosaic_DLRcontrol_7200.jpg

### Jupiter / cassini_pia07782

- **agency**: NASA
- **mission**: Cassini
- **instrument**: ISS
- **description**: Cassini December 2000 Jupiter cylindrical mosaic (NASA Photojournal PIA07782)
- **provenance**: Wikimedia Commons (NASA/JPL Photojournal PIA07782)
- **license**: Public Domain (NASA/JPL/SSI)
- **citation**: NASA/JPL/Space Science Institute, Cassini ISS team, Photojournal PIA07782.
- **portal_url**: https://photojournal.jpl.nasa.gov/catalog/PIA07782
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/1/1e/Jupiter_Cylindrical_Map_-_Dec_2000_PIA07782.jpg

### Jupiter / sss

- **agency**: NASA
- **mission**: Cassini
- **instrument**: ISS (Imaging Science Subsystem)
- **description**: Jupiter global color map (Cassini Dec 2000 flyby), processed by Solar System Scope
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying Cassini ISS imagery is public domain (NASA/JPL/SSI)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA/JPL/Space Science Institute, Cassini ISS team.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_jupiter.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/5/5e/Solarsystemscope_texture_8k_jupiter.jpg

### Io / voyager_pia00319

- **agency**: NASA
- **mission**: Voyager 1/2
- **instrument**: ISS (narrow- and wide-angle)
- **description**: Io cylindrical map from Voyager imagery (NASA Photojournal PIA00319)
- **provenance**: Wikimedia Commons (NASA/JPL Photojournal PIA00319)
- **license**: Public Domain (NASA/JPL)
- **citation**: NASA/JPL, Photojournal PIA00319. Voyager Project, USGS.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Io_map_projection_PIA00319.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/0/04/Io_map_projection_PIA00319.jpg
- **note**: Image aspect 2.35:1 rather than exactly 2:1 — contains a thin annotated margin.

### Europa / voyager_galileo_usgs

- **agency**: NASA
- **mission**: Voyager + Galileo
- **instrument**: Voyager ISS, Galileo SSI
- **description**: Europa Voyager-Galileo SSI global mosaic (USGS), low resolution
- **provenance**: Wikimedia Commons (USGS Astrogeology)
- **license**: Public Domain (NASA/USGS)
- **citation**: USGS Astrogeology, Europa Voyager-Galileo SSI global mosaic.
- **portal_url**: https://astrogeology.usgs.gov/search/map/Europa/Voyager-Galileo/Europa_Voyager_GalileoSSI_global_mosaic_500m
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/2/26/Europa_Voyager_GalileoSSI_global_mosaic.jpg

### Ganymede / jonsson

- **agency**: NASA
- **mission**: Voyager + Galileo
- **instrument**: Voyager ISS, Galileo SSI
- **description**: Ganymede global map by Björn Jónsson, derived from NASA Voyager and Galileo imagery
- **provenance**: Wikimedia Commons / Björn Jónsson
- **license**: Public Domain (image author's release on Wikimedia Commons); underlying imagery NASA/JPL
- **citation**: Map by Björn Jónsson. Underlying data: NASA/JPL Voyager 1/2 and Galileo missions.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Map_of_Ganymede_by_Bj%C3%B6rn_J%C3%B3nsson.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/d/db/Map_of_Ganymede_by_Bj%C3%B6rn_J%C3%B3nsson.jpg

### Callisto / voyager_galileo_usgs

- **agency**: NASA
- **mission**: Voyager + Galileo
- **instrument**: Voyager ISS, Galileo SSI
- **description**: Callisto USGS global cylindrical map (small)
- **provenance**: Wikimedia Commons (USGS Astrogeology)
- **license**: Public Domain (NASA/USGS)
- **citation**: USGS Astrogeology, Callisto Voyager-Galileo SSI global mosaic.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Callisto_USGS_global_small.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/9/96/Callisto_USGS_global_small.jpg

### Saturn / sss

- **agency**: NASA
- **mission**: Cassini
- **instrument**: ISS
- **description**: Saturn global cloud-band mosaic, processed by Solar System Scope
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying Cassini ISS imagery is public domain (NASA/JPL/SSI)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA/JPL-Caltech/Space Science Institute.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_8k_saturn.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/1/1e/Solarsystemscope_texture_8k_saturn.jpg

### Enceladus / cassini_pia14937

- **agency**: NASA
- **mission**: Cassini
- **instrument**: ISS
- **description**: Enceladus global photomosaic (PIA14937, December 2011)
- **provenance**: Wikimedia Commons (NASA/JPL Photojournal PIA14937)
- **license**: Public Domain (NASA/JPL/SSI)
- **citation**: NASA/JPL/SSI Cassini ISS team, Photojournal PIA14937.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Map_of_Enceladus_PIA_14937_Dec_2011.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/3/37/Map_of_Enceladus_PIA_14937_Dec_2011.jpg

### Rhea / cassini_pia12561

- **agency**: NASA
- **mission**: Cassini
- **instrument**: ISS
- **description**: Rhea global cylindrical map from Cassini ISS (PIA12561)
- **provenance**: Wikimedia Commons (NASA/JPL Photojournal PIA12561)
- **license**: Public Domain (NASA/JPL/SSI)
- **citation**: NASA/JPL/SSI Cassini ISS team, Photojournal PIA12561.
- **portal_url**: https://commons.wikimedia.org/wiki/File:PIA12561_Rhea_Map.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/1/1c/PIA12561_Rhea_Map.jpg

### Iapetus / cassini_color

- **agency**: NASA
- **mission**: Cassini
- **instrument**: ISS
- **description**: Iapetus color global map from Cassini ISS
- **provenance**: Wikimedia Commons (NASA/JPL/SSI)
- **license**: Public Domain (NASA/JPL/SSI)
- **citation**: NASA/JPL/SSI Cassini ISS team.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Iapetus_Color_Map.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/5/53/Iapetus_Color_Map.jpg

### Titan / cassini_iss_polar

- **agency**: NASA / ESA
- **mission**: Cassini-Huygens
- **instrument**: Cassini ISS / VIMS / RADAR
- **description**: Global Titan mosaic from Cassini ISS
- **provenance**: USGS Astrogeology
- **license**: Public Domain (NASA/JPL/SSI); Cassini-Huygens is a joint NASA/ESA/ASI mission
- **citation**: NASA/JPL/SSI/USGS Astrogeology.
- **portal_url**: https://astrogeology.usgs.gov/search/map/Titan/Cassini/Global-Mosaic/Titan_ISS_Globe_Polar_Stereographic
- **note**: No clean 2:1 equirectangular file at Wikimedia; download manually from USGS.

### Uranus / sss

- **agency**: NASA
- **mission**: Voyager 2
- **instrument**: ISS
- **description**: Featureless cloud-deck composite, Solar System Scope
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying Voyager 2 imagery is public domain (NASA/JPL)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA/JPL Voyager 2 imaging team (1986).
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_2k_uranus.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/9/95/Solarsystemscope_texture_2k_uranus.jpg

### Neptune / sss

- **agency**: NASA
- **mission**: Voyager 2 / Hubble
- **instrument**: Voyager 2 ISS, HST WFC3
- **description**: Neptune cloud composite, Solar System Scope
- **provenance**: Wikimedia Commons / Solar System Scope (INOVE s.r.o.)
- **license**: CC BY 4.0 (texture); underlying Voyager 2 / HST imagery is public domain (NASA/JPL/STScI)
- **citation**: Solar System Scope (CC BY 4.0). Underlying data: NASA/JPL Voyager 2 (1989); STScI/Hubble.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Solarsystemscope_texture_2k_neptune.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/1/1e/Solarsystemscope_texture_2k_neptune.jpg

### Triton / voyager

- **agency**: NASA
- **mission**: Voyager 2
- **instrument**: ISS
- **description**: Triton global cylindrical map from Voyager 2 1989 flyby
- **provenance**: Wikimedia Commons (NASA/JPL/USGS)
- **license**: Public Domain (NASA/JPL)
- **citation**: NASA/JPL Voyager 2 imaging team (1989); USGS Astrogeology.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Triton_map_no_grid.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/6/61/Triton_map_no_grid.jpg

### Pluto / new_horizons

- **agency**: NASA
- **mission**: New Horizons
- **instrument**: LORRI / MVIC
- **description**: Pluto global cylindrical map at 600 m/pixel from New Horizons July 2015 flyby
- **provenance**: Wikimedia Commons (NASA/JHU-APL/SwRI New Horizons)
- **license**: Public Domain (NASA)
- **citation**: NASA/JHU-APL/SwRI, New Horizons LORRI/MVIC team, 2015.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Pmap_cyl_HR_LOR_600m.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/1/1b/Pmap_cyl_HR_LOR_600m.jpg

### Charon / new_horizons

- **agency**: NASA
- **mission**: New Horizons
- **instrument**: LORRI / MVIC
- **description**: Charon global cylindrical map from New Horizons (PS717 high-res, 180°-centered)
- **provenance**: Wikimedia Commons (NASA/JHU-APL/SwRI New Horizons)
- **license**: Public Domain (NASA)
- **citation**: NASA/JHU-APL/SwRI New Horizons LORRI/MVIC team, 2015.
- **portal_url**: https://commons.wikimedia.org/wiki/File:Cpmap_cyl_PS717_HR_180.jpg
- **asset_url**: https://upload.wikimedia.org/wikipedia/commons/f/f8/Cpmap_cyl_PS717_HR_180.jpg

### bw / daynight

- **agency**: implanet
- **mission**: synthetic
- **instrument**: procedural
- **description**: Day-night hemisphere reference texture: white day hemisphere centred on lon 0 (+X), GREY shaded hemisphere centred on lon ±180 (grey, not black, so the night side stays legible), overlaid with a 30° graticule so the projected disk reads as a globe. Latitude-independent; render flat (no sun_direction / ambient=1.0) to verify which hemisphere a view_direction shows.
- **provenance**: Generated by implanet.assets._synthetic
- **license**: Public Domain (implanet)
- **citation**: implanet synthetic reference texture.
- **portal_url**: generated locally by implanet.assets (no download)

---

## SPICE kernels

### naif_lsk  (naif0012.tls)

- **category**: generic
- **description**: Leapseconds kernel (LSK) — UTC<->ET time conversion.
- **provenance**: NAIF generic kernels
- **license**: Public Domain (NASA/NAIF)
- **url**: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls

### naif_pck  (pck00011.tpc)

- **category**: generic
- **description**: Planetary constants kernel (PCK) — body radii and IAU rotation models.
- **provenance**: NAIF generic kernels
- **license**: Public Domain (NASA/NAIF)
- **url**: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc

### de440s  (de440s.bsp)

- **category**: generic
- **description**: JPL DE440s planetary ephemeris (1849-2150). Sun, planet barycenters, plus Mercury/Venus/Earth/Moon centers.
- **provenance**: NAIF generic kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp

### jup_satellites  (jup365.bsp)

- **category**: satellite
- **description**: JUP365 Jovian satellite ephemeris (1600-2200). The only NAIF generic file carrying the Galilean moon centers (501-504).
- **provenance**: NAIF generic kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/jup365.bsp

### nep_satellites  (nep105.bsp)

- **category**: satellite
- **description**: NEP105 Neptunian satellite ephemeris. Provides Triton's body center (801).
- **provenance**: NAIF generic kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/nep105.bsp

### messenger_cruise  (msgr_040803_080216_120401.bsp)

- **category**: spacecraft
- **description**: MESSENGER reconstructed trajectory. Covers the Mercury M1 flyby (2008-01-14) and the Venus V2 flyby (2007-06-05).
- **provenance**: NAIF/PDS MESSENGER SPICE archive
- **license**: Public Domain (NASA/JHU-APL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/pds/data/mess-e_v_h-spice-6-v1.0/messsp_1000/data/spk/msgr_040803_080216_120401.bsp

### voyager1_jupiter  (vgr1_jup230.bsp)

- **category**: spacecraft
- **description**: Voyager 1 Jupiter-encounter trajectory (spacecraft only; pair with jup_satellites for moon flybys).
- **provenance**: NAIF VOYAGER kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/VOYAGER/kernels/spk/vgr1_jup230.bsp

### voyager1_saturn  (vgr1_sat337.bsp)

- **category**: spacecraft
- **description**: Voyager 1 Saturn-encounter trajectory.
- **provenance**: NAIF VOYAGER kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/VOYAGER/kernels/spk/vgr1_sat337.bsp

### voyager2_uranus  (vgr2.ura182.bsp)

- **category**: spacecraft
- **description**: Voyager 2 Uranus-encounter trajectory (also carries Uranian moon centers 701-705).
- **provenance**: NAIF VOYAGER kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/VOYAGER/kernels/spk/vgr2.ura182.bsp

### voyager2_neptune  (vgr2_nep097.bsp)

- **category**: spacecraft
- **description**: Voyager 2 Neptune-encounter trajectory (covers both the Neptune and Triton close approaches).
- **provenance**: NAIF VOYAGER kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/VOYAGER/kernels/spk/vgr2_nep097.bsp

### voyager2_saturn  (vgr2_sat337.bsp)

- **category**: spacecraft
- **description**: Voyager 2 Saturn-encounter trajectory.
- **provenance**: NAIF VOYAGER kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/VOYAGER/kernels/spk/vgr2_sat337.bsp

### new_horizons_pluto  (nh_recon_pluto_od122_v01.bsp)

- **category**: spacecraft
- **description**: New Horizons reconstructed Pluto-encounter trajectory. Contains the spacecraft (-98) AND Pluto-system body centers (Pluto 999, Charon 901, ...). Note: nh_plu047_od122.bsp has the bodies but NOT the spacecraft.
- **provenance**: NAIF/PDS New Horizons SPICE archive
- **license**: Public Domain (NASA/JHU-APL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/pds/data/nh-j_p_ss-spice-6-v1.0/nhsp_1000/data/spk/nh_recon_pluto_od122_v01.bsp

### dawn_cruise  (dawn_rec_081109_090228_090306_v1.bsp)

- **category**: spacecraft
- **description**: Dawn reconstructed cruise trajectory covering the 2009-02-18 Mars gravity assist.
- **provenance**: NAIF/PDS Dawn SPICE archive
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/pds/data/dawn-m_a-spice-6-v1.0/dawnsp_1000/data/spk/dawn_rec_081109_090228_090306_v1.bsp

### galileo_cruise  (s970311a.bsp)

- **category**: spacecraft
- **description**: Galileo interplanetary-cruise trajectory. Covers the 1990-02-10 Venus flyby.
- **provenance**: NAIF GLL kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/GLL/kernels/spk/s970311a.bsp

### galileo_tour  (gll_951120_021126_raj2021.bsp)

- **category**: spacecraft
- **description**: Galileo reconstructed Jupiter-tour trajectory. Covers every targeted Galilean-moon encounter.
- **provenance**: NAIF GLL kernels
- **license**: Public Domain (NASA/JPL)
- **url**: https://naif.jpl.nasa.gov/pub/naif/GLL/kernels/spk/gll_951120_021126_raj2021.bsp
