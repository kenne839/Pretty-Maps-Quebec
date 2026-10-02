========================================================================
LAC DUFRESNE NAUTICAL CARTOGRAPHY PROJECT
========================================================================

1. PROJECT OVERVIEW
------------------------------------------------------------------------
This project compiles publication-grade bathymetric and topographic charts 
of Lac Dufresne (Lantier, Quebec). 

It merges multiple spatial sources:
- Official Quebec / CanVec 50k surveyed lake waterbodies
- Université de Montréal (2010) bathymetric depth surveys (isobaths & pits)
- High-resolution digital elevation models (DEM) for terrestrial contours
- OpenStreetMap networks for local and regional roadways and outlet hydrology


2. CURRENT SCRIPT STATUS
------------------------------------------------------------------------
The project has been consolidated into a single master script (`script.py`)
with all configurations unified at the top:

* Active Configuration:
  - Default Style : "NAUTICAL_POSTER"
  - Supported Sizes: "18X24", "METAL", "ORIGINAL"
  - Default Size  : "18X24" (or set to "METAL" for metal prints)
  - Palettes      : Batched rendering across 5 curated themes

* Bathymetric & Cartographic Styling:
  - Contours: Sequential 2 m interval isobaths (2 m through 14 m) labeled 
    along curve tangents (`frac = 0.50`) with white stroke halos.
  - Deep Point: Survey fossa marked by a standalone "+" crosshair.
  - Hydrology: Southern outlet stream extracted and routed under the road network.
  - Landmarks: Cabin coordinates set for "Hytta" with offset label placement.
  - Marginalia: Multi-point nautical compass rose, neatline double border, 
    color-coded depth bar legend, and segmented metric scale bar (1:12,000).


3. DIRECTORY STRUCTURE
------------------------------------------------------------------------
Pretty Maps Quebec/
│
├── .venv/                      # Python virtual environment
├── .gitignore                  # Git ignore rules (.venv, cache files)
├── options/                    # Batched output charts (PDF & PNG)
│   ├── lac_dufresne_18x24_admiralty.pdf
│   ├── lac_dufresne_18x24_admiralty.png
│   ├── lac_dufresne_metal_admiralty.png
│   └── ...
│
├── script.py                   # Master cartographic generator (consolidated)
├── extract_lake.py             # Preprocessor to extract/dissolve CanVec lake body
├── find_dufresne.py            # Diagnostic coordinate/bounding box helper
├── insepct_gpkg.py             # Layer & CRS inspection tool for GeoPackages
├── get_dem.py                  # DEM clipping & bounding box helper
│
├── 01374_Dufresne.gpkg         # Bathymetric contours and sounding pits
├── lake_shoreline.gpkg         # Surveyed shoreline geometry
├── dem_dufresne.tif            # Terrestrial elevation raster
└── lac_dufresne.osm            # Road network and surface water waterways


4. SCRIPT CONFIGURATION OPTIONS
------------------------------------------------------------------------
Settings at the top of `script.py`:

A. `STYLE_MODE`
   - "NAUTICAL_POSTER"   : Complete map composition with neatlines, parchment/paper 
                           washes, legends, scale, and metadata blocks.
   - "TRANSPARENT_BLACK" : Clean, minimalist black linework on an alpha-transparent 
                           canvas suitable for laser cutting, CNC, or overlays.

B. `POSTER_SIZE`
   - "18X24"    : Standard North American large poster (24" canvas height, width ~17.65").
                  Scaling factor SF = 1.5, rendered at 300 DPI (PDF & PNG).
   - "METAL"    : European / Displate standard metal poster (12.6" × 17.7" / 32cm × 45cm).
                  Scaling factor SF = 1.15, super-sampled at ultra-sharp 600 DPI (7,560 × 10,620 px).
                  Automatically expands geographic bounds symmetrically to conform exactly to the 
                  12.6 : 17.7 frame ratio without distortion. Outputs raster PNGs only, as commercial 
                  metal print vendors require high-resolution image files.
   - "ORIGINAL" : Baseline wall print (~12" × 16"). Baseline scaling factor SF = 1.0 at 300 DPI.

C. `PALETTES` (Batched across all 5 themes)
   - "ADMIRALTY"       : Crisp alabaster background (#FAF9F6) with marine navy, 
                         deep cyan contours, and coastal blue washes.
   - "CLASSIC_HYDRO"   : Warm linen background (#FBF9F4) with vintage teal washes 
                         and dark slate inks.
   - "NORDIC_MOSS"     : Scandinavian limestone paper (#F3F4F1) with muted sage 
                         and deep spruce gradients.
   - "COPPERPLATE"     : Antique tea-stained vellum (#F4EBD9) with verdigris patina 
                         fills and sepia/burnt umber linework.
   - "BLUEPRINT"       : High-contrast cyanotype/sonar theme with dark navy paper 
                         (#121C24) and glowing azure/cyan contours.


5. OUTPUTS & PRINT CONSIDERATIONS
------------------------------------------------------------------------
* Metal Print Considerations (`POSTER_SIZE = "METAL"`):
  - Canvas Aspect Ratio : 12.6" × 17.7" (1 : 1.405 ratio, matching Displate Medium size).
  - Resolution          : 600 DPI super-sampling results in 7,560 × 10,620 pixel masters.
  - Geometry Adaptation : Symmetrically pads either latitude or longitude so the map fills
                          the plate without stretching or artificial letterboxing.
  - File Format         : PNG raster only. Professional metal photo-labs require high-DPI 
                          raster files (PNG or converted 100% quality JPEG) rather than PDFs.

* Paper Wall Poster (`POSTER_SIZE = "18X24"`):
  - Vector PDF (`.pdf`) : Infinite resolution for commercial plotters and offset printing.
  - Raster PNG (`.png`) : 300 DPI high-resolution proofing copy (~5,295 × 7,200 px).
  - Print Frame Extent  : Maps to ~17.65" × 24.00" to preserve geographic ground aspect ratio,
                          fitting standard 18" × 24" poster frames with minimal matting.


6. USAGE
------------------------------------------------------------------------
Run in a PowerShell terminal:

1. Navigate to the folder:
   cd "C:\Users\Michael\Documents\Python\Pretty Maps Quebec"

2. Activate the virtual environment:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   .\.venv\Scripts\Activate.ps1

3. Execute the script:
   python .\script.py

Generated files are placed in the `options/` directory.
========================================================================