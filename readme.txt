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
The main script (`script.py`) is configured with:

* Active Configuration:
  - Default Style : "NAUTICAL_POSTER"
  - Default Size  : "18X24" (Standard wall poster scale, SF = 1.5)
  - Default Theme : "ADMIRALTY" (Modern crisp hydrographic navy/ocean fills)

* Bathymetric & Cartographic Styling:
  - Contours: Sequential 2 m interval isobaths (2 m through 14 m) labeled 
    along line tangents (`frac = 0.50`) with white stroke halos.
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
├── OUTPUT/                     # Generated charts (PDF & PNG)
│   ├── lac_dufresne_18x24_admiralty.pdf
│   ├── lac_dufresne_18x24_admiralty.png
│   └── ...
│
├── script.py                   # Master cartographic generator
├── extract_lake.py             # Preprocessor to extract/dissolve CanVec lake body
├── find_dufresne.py            # Diagnostic coordinate/bounding box helper
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
                           canvas suitable for laser cutting or overlays.

B. `POSTER_SIZE`
   - "18X24"    : 24.0" canvas height with scaled factor `SF = 1.5` for all text, 
                  line weights, casings, and symbols.
   - "ORIGINAL" : 16.0" canvas height with baseline factor `SF = 1.0` (~12"x16").

C. `PALETTE`
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
* Vector PDF (`.pdf`):
  Always use the generated PDF for professional large-format printing. Text, 
  cased roads, neatlines, and contour vectors are preserved with infinite 
  resolution on commercial plotters.

* Raster Preview (`.png`):
  Rendered at 300 DPI for high-resolution screen viewing, proofing, or digital 
  sharing.

* Print Frame Dimensions:
  At `POSTER_SIZE = "18X24"`, the map extent calculates to ~17.65" × 24.00" 
  to preserve true geographic aspect ratio without coordinate distortion. 
  This fits cleanly into standard off-the-shelf 18" × 24" poster frames with 
  a minor ~0.17" border tolerance under the frame rabbet or matting.


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

Generated files are placed in the `OUTPUT/` directory.
========================================================================