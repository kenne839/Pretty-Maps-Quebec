from pathlib import Path
import geopandas as gpd

# Replace with the actual unzipped .shp filename (e.g., elevation_l.shp, courbe_niveau.shp, etc.)
SHP_PATH = Path("elevation_l.shp")

# Study area bounds for Lac Dufresne
WEST, SOUTH, EAST, NORTH = -74.26, 46.185, -74.20, 46.23
BBOX = (WEST, SOUTH, EAST, NORTH)

print(f"Reading target bounding box from {SHP_PATH.name}...")

# Pass bbox to pyogrio/GDAL to bypass reading the rest of Quebec into memory
try:
    topo_gdf = gpd.read_file(SHP_PATH, bbox=BBOX)
except Exception:
    # If source is projected (e.g. MTM or UTM NAD83), reproject the bbox first
    import pyogrio
    info = pyogrio.read_info(SHP_PATH)
    crs = info["crs"]
    
    bbox_gdf = gpd.GeoDataFrame(geometry=[gpd.points_from_xy([WEST, EAST], [SOUTH, NORTH])], crs="EPSG:4326").to_crs(crs)
    minx, miny, maxx, maxy = bbox_gdf.total_bounds
    topo_gdf = gpd.read_file(SHP_PATH, bbox=(minx, miny, maxx, maxy)).to_crs(epsg=4326)

print(f"Retrieved {len(topo_gdf)} contour segments.")

# Save local cut
out_gpkg = Path("topo_dufresne.gpkg")
topo_gdf.to_file(out_gpkg, layer="contours", driver="GPKG")
print(f"Saved local contours to: {out_gpkg.resolve()}")