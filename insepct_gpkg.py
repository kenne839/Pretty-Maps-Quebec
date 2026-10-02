from pathlib import Path
import geopandas as gpd
import pyogrio

folder = Path(__file__).resolve().parent
gpkg_files = list(folder.glob("*.gpkg"))
if not gpkg_files:
    print("Error: No .gpkg file found in this folder!")
    exit()

gpkg_path = gpkg_files[0]
print(f"Inspecting file: {gpkg_path.name}\n" + "="*50)

layers = [l[0] for l in pyogrio.list_layers(gpkg_path)]
print(f"Layers found: {layers}\n")

for layer_name in layers:
    print(f"--- Layer: {layer_name} ---")
    gdf = gpd.read_file(gpkg_path, layer=layer_name)
    print(f"Feature count : {len(gdf)}")
    print(f"Geometry type : {gdf.geometry.geom_type.value_counts().to_dict()}")
    print(f"Native CRS    : {gdf.crs}")
    
    # Convert to WGS84 to see real GPS bounding box
    if gdf.crs:
        gdf_wgs84 = gdf.to_crs(epsg=4326)
        minx, miny, maxx, maxy = gdf_wgs84.total_bounds
        print(f"WGS84 Lon Min/Max (X): {minx:.6f} to {maxx:.6f}")
        print(f"WGS84 Lat Min/Max (Y): {miny:.6f} to {maxy:.6f}")
        print(f"Center Coordinate    : Lat {(miny+maxy)/2:.6f}, Lon {(minx+maxx)/2:.6f}")
    print()