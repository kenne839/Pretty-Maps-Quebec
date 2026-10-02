import math
import xml.etree.ElementTree as ET
from pathlib import Path as FilePath
import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Polygon as MplPolygon
import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from shapely.geometry import box, LineString, MultiLineString, MultiPolygon, Point, Polygon
from shapely.ops import polygonize, unary_union

# ==========================================
# CONFIGURATION
# Options for STYLE_MODE:  "NAUTICAL_POSTER" or "TRANSPARENT_BLACK"
# Options for POSTER_SIZE: "ORIGINAL" (~12x16) or "18X24"
# ==========================================
STYLE_MODE  = "NAUTICAL_POSTER"
POSTER_SIZE = "18X24"

BASE_DIR = FilePath(__file__).resolve().parent

OSM_FILE = BASE_DIR / "lac_dufresne.osm"
GPKG_FILE = BASE_DIR / "01374_Dufresne.gpkg"
LAKE_SHORELINE_FILE = BASE_DIR / "lake_shoreline.gpkg"
DEM_FILE = BASE_DIR / "dem_dufresne.tif"

DEPTH_LAYER = "iso_01374_2010_CCREL"
PIT_LAYER = "fos_01374_2010_CCREL"

CABIN_COORDS = (-74.219638, 46.209417)

# Reduced threshold to only delete true noise/artifacts (~50 sq meters)
MIN_DEPTH_AREA = 0.00000005 
MIN_CONTOUR_LENGTH = 0.0002

# New output directory for the batched options
OPTIONS_DIR = BASE_DIR / "options"
OPTIONS_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------
# 1. Palette Dictionaries
# ------------------------------------------
PALETTES = {
    "CLASSIC_HYDRO": {
        "LAND_BG": "#FBF9F4",
        "WATER_BASE": "#D8EFF0",
        "SHORE_INK": "#183B38",
        "CONTOUR_INK": "#32625F",
        "SOUNDING_INK": "#1D4744",
        "STREAM_COLOR": "#266986",
        "TOPO_COLOR": "#D8D1C3",
        "ROAD_CASING": "#FFFFFF",
        "ROAD_CORE": "#2B2D2F",
        "ROAD_MAJOR": "#181A1B",
        "MAIN_INK": "#181A1B",
        "META_INK": "#5A6065",
        "CABIN_ACCENT": "#9A2A2A",
        "GRADIENT": ["#C4E8E5", "#A4DBD4", "#82CAC0", "#67B8AD", "#51A499"]
    },
    "ADMIRALTY": {
        "LAND_BG": "#FAF9F6",
        "WATER_BASE": "#E8F4F8",
        "SHORE_INK": "#0E2530",
        "CONTOUR_INK": "#2C5E6E",
        "SOUNDING_INK": "#1A404D",
        "STREAM_COLOR": "#245A6D",
        "TOPO_COLOR": "#E0DCD3",
        "ROAD_CASING": "#FFFFFF",
        "ROAD_CORE": "#2F353B",
        "ROAD_MAJOR": "#14181B",
        "MAIN_INK": "#0D161B",
        "META_INK": "#505A61",
        "CABIN_ACCENT": "#C0392B",
        "GRADIENT": ["#D2EAF0", "#B2DBE4", "#8FC8D5", "#6AAFC0", "#4B94A7"]
    },
    "NORDIC_MOSS": {
        "LAND_BG": "#F3F4F1",
        "WATER_BASE": "#D8DFD8",
        "SHORE_INK": "#242D26",
        "CONTOUR_INK": "#455248",
        "SOUNDING_INK": "#2E3A31",
        "STREAM_COLOR": "#4A6356",
        "TOPO_COLOR": "#DDDED8",
        "ROAD_CASING": "#FFFFFF",
        "ROAD_CORE": "#3D443F",
        "ROAD_MAJOR": "#242D26",
        "MAIN_INK": "#1C211D",
        "META_INK": "#5B635D",
        "CABIN_ACCENT": "#B85D3B",
        "GRADIENT": ["#C5D0C6", "#A8B8AA", "#8B9E8E", "#6F8573", "#566C5A"]
    },
    "COPPERPLATE": {
        "LAND_BG": "#F4EBD9",
        "WATER_BASE": "#D5E2D5",
        "SHORE_INK": "#2B2319",
        "CONTOUR_INK": "#3B4A3E",
        "SOUNDING_INK": "#2C372F",
        "STREAM_COLOR": "#3C635B",
        "TOPO_COLOR": "#DFD2BC",
        "ROAD_CASING": "#FBF8F0",
        "ROAD_CORE": "#3D342B",
        "ROAD_MAJOR": "#231C14",
        "MAIN_INK": "#231C14",
        "META_INK": "#665749",
        "CABIN_ACCENT": "#8A281E",
        "GRADIENT": ["#BED2C0", "#A2C1A6", "#83AC8A", "#65966E", "#4B7E55"]
    },
    "BLUEPRINT": {
        "LAND_BG": "#121C24",
        "WATER_BASE": "#162E3B",
        "SHORE_INK": "#6BD2F7",
        "CONTOUR_INK": "#3A87A6",
        "SOUNDING_INK": "#B0E6F9",
        "STREAM_COLOR": "#48A3C7",
        "TOPO_COLOR": "#1F2E3A",
        "ROAD_CASING": "#0D141A",
        "ROAD_CORE": "#3A4A57",
        "ROAD_MAJOR": "#5A7285",
        "MAIN_INK": "#E8F4F8",
        "META_INK": "#8EA2B0",
        "CABIN_ACCENT": "#FF6B4A",
        "GRADIENT": ["#193E50", "#1C516A", "#206889", "#2480AB", "#2CA0D6"]
    }
}

# ------------------------------------------
# 2. Load Bathymetry & Proportional Dimensions
# ------------------------------------------
print(f"1/4 Loading bathymetry contours from GeoPackage...")
depth_gdf = gpd.read_file(GPKG_FILE, layer=DEPTH_LAYER).to_crs(epsg=4326)
pit_gdf = gpd.read_file(GPKG_FILE, layer=PIT_LAYER).to_crs(epsg=4326)

minx, miny, maxx, maxy = depth_gdf.total_bounds
pad_x = (maxx - minx) * 0.40
pad_y = (maxy - miny) * 0.40

WEST, EAST = minx - pad_x, maxx + pad_x
SOUTH, NORTH = miny - pad_y, maxy + pad_y
MID_LAT = (NORTH + SOUTH) / 2.0

lon_span = EAST - WEST
lat_span = NORTH - SOUTH
aspect_correction = 1.0 / math.cos(math.radians(MID_LAT))

if POSTER_SIZE == "18X24":
    fig_height = 24.0
    fig_width = fig_height * (lon_span / (lat_span * aspect_correction))
    SF = 1.5
else:
    fig_height = 16.0
    fig_width = fig_height * (lon_span / (lat_span * aspect_correction))
    SF = 1.0

compass_x = WEST + lon_span * 0.82
compass_y = SOUTH + lat_span * 0.84
rad_x = lon_span * 0.045
rad_y = rad_x * aspect_correction

lac_creux_label_x = WEST + lon_span * 0.075
lac_creux_label_y = SOUTH + lat_span * 0.165

compass_exclusion = box(
    compass_x - rad_x * 1.8,
    compass_y - rad_y * 1.8,
    compass_x + rad_x * 3.8,
    compass_y + rad_y * 2.6
)

title_legend_block = box(
    WEST + lon_span * 0.05,
    SOUTH + lat_span * 0.60,
    WEST + lon_span * 0.44,
    SOUTH + lat_span * 0.96
)

sb_deg_len = (500.0 / 1000.0) / (111.320 * math.cos(math.radians(MID_LAT)))
sb_w = sb_deg_len / lon_span
sb_x0 = 0.72
sb_y0 = 0.035
sb_h = 0.008

scale_bar_box = box(
    WEST + lon_span * (sb_x0 - 0.02),
    SOUTH + lat_span * (sb_y0 - 0.02),
    WEST + lon_span * (sb_x0 + sb_w + 0.03),
    SOUTH + lat_span * (sb_y0 + 0.06)
)

cabin_label_box = box(
    CABIN_COORDS[0] - 0.0004,
    CABIN_COORDS[1] - 0.0008,
    CABIN_COORDS[0] + 0.0030,
    CABIN_COORDS[1] + 0.0008
)

# ------------------------------------------
# 3. Survey Shoreline, DEM & Roads
# ------------------------------------------
print("2/4 Loading official surveyed shoreline...")
if not FilePath(LAKE_SHORELINE_FILE).exists():
    raise FileNotFoundError(f"Missing '{LAKE_SHORELINE_FILE}'. Run extract_lake.py first.")

lake_gdf = gpd.read_file(LAKE_SHORELINE_FILE, layer="shoreline").to_crs(epsg=4326)
lake_union = lake_gdf.union_all()

if not lake_union.is_empty and lake_union.intersects(compass_exclusion):
    lake_union = lake_union.difference(compass_exclusion)

lake_gdf = gpd.GeoDataFrame(geometry=[lake_union], crs="EPSG:4326")

print("3/4 Indexing roads and streams...")
tree = ET.parse(OSM_FILE)
root = tree.getroot()

nodes = {
    node.attrib["id"]: (float(node.attrib["lon"]), float(node.attrib["lat"]))
    for node in root.findall("node")
}

primary_lines, secondary_lines, local_lines = [], [], []
all_roads = []
candidate_stream_lines = []

PRIMARY_TAGS = {"motorway", "trunk", "primary", "secondary"}
SECONDARY_TAGS = {"tertiary", "unclassified"}
LOCAL_TAGS = {"residential", "living_street", "service", "track"}

for way in root.findall("way"):
    tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
    coords = [nodes[nd.attrib["ref"]] for nd in way.findall("nd") if nd.attrib["ref"] in nodes]
    if len(coords) < 2:
        continue

    waterway = tags.get("waterway")
    if waterway in {"stream", "ditch", "drain", "river"}:
        candidate_stream_lines.append(LineString(coords))
        continue

    hw = tags.get("highway")
    if hw:
        all_roads.append(LineString(coords))
        if hw in PRIMARY_TAGS:
            primary_lines.append(coords)
        elif hw in SECONDARY_TAGS:
            secondary_lines.append(coords)
        elif hw in LOCAL_TAGS:
            local_lines.append(coords)

outlet_corridor = box(-74.245, 46.185, -74.210, 46.208)
road_network_union = unary_union(all_roads) if all_roads else None

selected_outlet_streams = []
for s_line in candidate_stream_lines:
    if s_line.intersects(outlet_corridor):
        if road_network_union is not None and s_line.intersects(road_network_union.buffer(0.0003)):
            selected_outlet_streams.append(s_line)
        elif s_line.centroid.y < 46.204:
            selected_outlet_streams.append(s_line)

stream_clip_mask = unary_union([lake_union, compass_exclusion, title_legend_block, cabin_label_box, scale_bar_box])

clipped_stream_lines = []
for s_line in selected_outlet_streams:
    if not stream_clip_mask.is_empty and s_line.intersects(stream_clip_mask):
        diff = s_line.difference(stream_clip_mask)
        if not diff.is_empty:
            geoms = [diff] if diff.geom_type == "LineString" else getattr(diff, "geoms", [])
            for g in geoms:
                if g.geom_type == "LineString" and len(g.coords) >= 2:
                    clipped_stream_lines.append(list(g.coords))
    else:
        clipped_stream_lines.append(list(s_line.coords))

dem_x_grid, dem_y_grid, dem_elev_smooth = None, None, None
dem_path = FilePath(DEM_FILE)
if dem_path.exists():
    try:
        with rasterio.open(dem_path) as dem:
            raw_elev = dem.read(1).astype(float)
            dem_elev_smooth = gaussian_filter(raw_elev, sigma=0.5, mode="reflect")
            cols = np.arange(dem.width)
            rows = np.arange(dem.height)
            xs, _ = rasterio.transform.xy(dem.transform, [0] * len(cols), cols)
            _, ys = rasterio.transform.xy(dem.transform, rows, [0] * len(rows))
            dem_x_grid, dem_y_grid = np.meshgrid(xs, ys)
    except Exception as e:
        print(f"Notice: DEM processing issue ({e})")

# ------------------------------------------
# Depth Gradient Fills & Isobath Labels (Rigid Color Mapping)
# ------------------------------------------
depth_col = next((c for c in depth_gdf.columns if any(k in c.lower() for k in ["prof", "depth", "val", "iso"])), None)
contour_labels = []
raw_depth_bands = []

master_depth_vals = []

if depth_col and depth_gdf[depth_col].dtype in [np.float64, np.int64, float, int]:
    master_depth_vals = sorted([float(v) for v in depth_gdf[depth_col].dropna().unique() if float(v) > 0.0])
    
    for d in master_depth_vals:
        subset = depth_gdf[depth_gdf[depth_col] >= d]
        merged_lines = subset.geometry.union_all()
        polys = list(polygonize(merged_lines))

        valid_polys = [p for p in polys if p.area >= MIN_DEPTH_AREA]
        
        if valid_polys:
            poly_union = unary_union(valid_polys)
            clipped = poly_union.intersection(lake_union)
            if not clipped.is_empty:
                if clipped.geom_type == "MultiPolygon":
                    kept_parts = [part for part in clipped.geoms if part.area >= MIN_DEPTH_AREA]
                    if kept_parts:
                        raw_depth_bands.append((float(d), unary_union(kept_parts)))
                elif clipped.area >= MIN_DEPTH_AREA:
                    raw_depth_bands.append((float(d), clipped))

    exploded_lines = []
    for _, row in depth_gdf.iterrows():
        val = float(row[depth_col])
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type == "LineString":
            exploded_lines.append((val, geom))
        elif geom.geom_type == "MultiLineString":
            for part in geom.geoms:
                if not part.is_empty:
                    exploded_lines.append((val, part))

    target_depths = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0]
    for td in target_depths:
        candidates = [line for val, line in exploded_lines if abs(val - td) < 0.1 and line.length > 0.003]
        if not candidates:
            continue
        candidates.sort(key=lambda g: g.length, reverse=True)
        chosen_line = candidates[0]

        frac = 0.50
        pt = chosen_line.interpolate(frac, normalized=True)

        delta = 0.002
        f0 = max(0.0, frac - delta)
        f1 = min(1.0, frac + delta)
        p0 = chosen_line.interpolate(f0, normalized=True)
        p1 = chosen_line.interpolate(f1, normalized=True)

        dx = (p1.x - p0.x) * aspect_correction
        dy = (p1.y - p0.y)
        angle_deg = math.degrees(math.atan2(dy, dx))

        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180

        contour_labels.append((pt.x, pt.y, str(int(round(td))), angle_deg))

def draw_compass_rose(ax, cx, cy, rx, ry, ink_color, bg_color):
    halo = mpatches.Ellipse((cx, cy), rx * 2.3, ry * 2.3, facecolor=bg_color, edgecolor="none", zorder=6.8)
    ax.add_patch(halo)

    pts = {
        'N': (cx, cy + ry),
        'S': (cx, cy - ry),
        'E': (cx + rx, cy),
        'W': (cx - rx, cy),
    }
    inner_rx, inner_ry = rx * 0.32, ry * 0.32
    diag = {
        'NE': (cx + inner_rx, cy + inner_ry),
        'SE': (cx + inner_rx, cy - inner_ry),
        'SW': (cx - inner_rx, cy - inner_ry),
        'NW': (cx - inner_rx, cy + inner_ry),
    }

    facets = [
        ([pts['N'], diag['NW'], (cx, cy)], True),
        ([pts['N'], diag['NE'], (cx, cy)], False),
        ([pts['E'], diag['NE'], (cx, cy)], True),
        ([pts['E'], diag['SE'], (cx, cy)], False),
        ([pts['S'], diag['SE'], (cx, cy)], True),
        ([pts['S'], diag['SW'], (cx, cy)], False),
        ([pts['W'], diag['SW'], (cx, cy)], True),
        ([pts['W'], diag['NW'], (cx, cy)], False),
    ]

    for poly_pts, filled in facets:
        ax.add_patch(MplPolygon(
            poly_pts,
            closed=True,
            facecolor=ink_color if filled else "none",
            edgecolor=ink_color,
            linewidth=0.8 * SF,
            zorder=7
        ))

    ax.text(
        pts['N'][0], pts['N'][1] + ry * 0.24, 'N',
        fontfamily="serif", fontsize=15 * SF, fontweight="bold",
        color=ink_color, ha="center", va="bottom", zorder=8,
        clip_on=True
    )

# ------------------------------------------
# 4. Render Output (Batched loop)
# ------------------------------------------
print(f"4/4 Rendering poster options...")

if STYLE_MODE == "NAUTICAL_POSTER":
    
    # Loop over every palette configuration in the dictionary
    for palette_name, active_palette in PALETTES.items():
        print(f" -> Rendering {palette_name}...")

        LAND_BG       = active_palette["LAND_BG"]
        WATER_BASE    = active_palette["WATER_BASE"]
        SHORE_INK     = active_palette["SHORE_INK"]
        CONTOUR_INK   = active_palette["CONTOUR_INK"]
        SOUNDING_INK  = active_palette["SOUNDING_INK"]
        STREAM_COLOR  = active_palette["STREAM_COLOR"]
        TOPO_COLOR    = active_palette["TOPO_COLOR"]
        ROAD_CASING   = active_palette["ROAD_CASING"]
        ROAD_CORE     = active_palette["ROAD_CORE"]
        ROAD_MAJOR    = active_palette["ROAD_MAJOR"]
        MAIN_INK      = active_palette["MAIN_INK"]
        META_INK      = active_palette["META_INK"]
        CABIN_ACCENT  = active_palette["CABIN_ACCENT"]

        fig = plt.figure(figsize=(fig_width, fig_height), facecolor=LAND_BG)
        ax = fig.add_axes([0.04, 0.04, 0.92, 0.92], facecolor=LAND_BG)

        if dem_elev_smooth is not None:
            min_elev = np.floor(np.nanmin(dem_elev_smooth) / 10.0) * 10
            max_elev = np.ceil(np.nanmax(dem_elev_smooth) / 10.0) * 10
            levels = np.arange(min_elev, max_elev, 10)

            ax.contour(
                dem_x_grid,
                dem_y_grid,
                dem_elev_smooth,
                levels=levels,
                colors=TOPO_COLOR,
                linewidths=0.45 * SF,
                alpha=0.75,
                zorder=0.5
            )

        if not lake_gdf.is_empty.all():
            lake_gdf.plot(
                ax=ax,
                facecolor=WATER_BASE,
                edgecolor=SHORE_INK,
                linewidth=1.3 * SF,
                aspect="auto",
                zorder=1.0
            )

        cmap = mcolors.LinearSegmentedColormap.from_list("bathymetry", active_palette["GRADIENT"])
        if raw_depth_bands and master_depth_vals:
            num_layers_expected = len(master_depth_vals)
            for depth_val, layer_geom in raw_depth_bands:
                idx = master_depth_vals.index(depth_val)
                c = cmap((idx + 1) / (num_layers_expected + 1))
                
                gpd.GeoDataFrame(geometry=[layer_geom], crs="EPSG:4326").plot(
                    ax=ax,
                    facecolor=c,
                    alpha=0.50, 
                    edgecolor="none",
                    aspect="auto",
                    zorder=1.1 + (idx * 0.05)
                )

        # Warning Fix: List comprehension applied directly to underlying Shapely geometries
        clean_depth_gdf = depth_gdf[[g.length >= MIN_CONTOUR_LENGTH if g else False for g in depth_gdf.geometry]]
        clean_depth_gdf.plot(
            ax=ax,
            color=CONTOUR_INK,
            linewidth=0.65 * SF,
            alpha=0.8,
            aspect="auto",
            zorder=2.0
        )

        for lx, ly, ltxt, lrot in contour_labels:
            ax.text(
                lx, ly, ltxt,
                rotation=lrot,
                rotation_mode="anchor",
                fontfamily="sans-serif",
                fontsize=6.8 * SF,
                fontweight="bold",
                color=SOUNDING_INK,
                ha="center",
                va="center",
                path_effects=[pe.withStroke(linewidth=2.8 * SF, foreground=WATER_BASE)],
                zorder=2.3
            )

        if not pit_gdf.empty:
            pit_gdf.plot(
                ax=ax,
                color=SHORE_INK,
                marker="+",
                markersize=80 * SF,
                linewidth=1.5 * SF,
                aspect="auto",
                zorder=2.4
            )

        if clipped_stream_lines:
            ax.add_collection(LineCollection(clipped_stream_lines, colors=STREAM_COLOR, linewidths=1.4 * SF, zorder=2.6))

        if local_lines:
            ax.add_collection(LineCollection(local_lines, colors=ROAD_CASING, linewidths=2.4 * SF, zorder=3.0))
        if secondary_lines:
            ax.add_collection(LineCollection(secondary_lines, colors=ROAD_CASING, linewidths=3.2 * SF, zorder=3.1))
        if primary_lines:
            ax.add_collection(LineCollection(primary_lines, colors=ROAD_CASING, linewidths=4.0 * SF, zorder=3.2))

        if local_lines:
            ax.add_collection(LineCollection(local_lines, colors=ROAD_CORE, linewidths=1.1 * SF, zorder=3.3))
        if secondary_lines:
            ax.add_collection(LineCollection(secondary_lines, colors=ROAD_CORE, linewidths=1.7 * SF, zorder=3.4))
        if primary_lines:
            ax.add_collection(LineCollection(primary_lines, colors=ROAD_MAJOR, linewidths=2.2 * SF, zorder=3.5))

        ax.scatter(
            [CABIN_COORDS[0]], [CABIN_COORDS[1]],
            s=85 * SF,
            marker="s",
            facecolor=CABIN_ACCENT,
            edgecolor=MAIN_INK,
            linewidth=1.1 * SF,
            zorder=5.0
        )
        ax.text(
            CABIN_COORDS[0] + 0.00035, CABIN_COORDS[1],
            "Hytta",
            fontfamily="serif",
            fontsize=8.5 * SF,
            fontstyle="italic",
            fontweight="bold",
            color=MAIN_INK,
            va="center",
            zorder=5.0,
            clip_on=True
        )

        ax.text(
            lac_creux_label_x, lac_creux_label_y,
            "Lac\nCreux",
            fontfamily="serif",
            fontsize=9.0 * SF,
            fontweight="bold",
            fontstyle="italic",
            color=SHORE_INK,
            ha="center",
            va="center",
            linespacing=1.1,
            zorder=5.0,
            clip_on=True
        )

        draw_compass_rose(ax, compass_x, compass_y, rad_x, rad_y, MAIN_INK, LAND_BG)

        ax.text(
            0.05, 0.94,
            "Lac Dufresne",
            transform=ax.transAxes,
            fontfamily="serif",
            fontsize=28 * SF,
            fontweight="bold",
            color=MAIN_INK,
            va="top",
            zorder=6.0
        )
        legend_meta = (
            "LANTIER, LAURENTIDES REGION, QUEBEC\n"
            "COORDINATES: 46° 12' 19\" N, 74° 13' 30\" W\n"
            "SURFACE AREA: 0.92 SQ KM (0.36 SQ MI) | ELEVATION: 465 M (1,526 FT)\n"
            "MAX DEPTH: 14.8 M (48.6 FT) | MEAN DEPTH: 5.4 M (17.7 FT)"
        )
        ax.text(
            0.05, 0.89,
            legend_meta,
            transform=ax.transAxes,
            fontfamily="serif",
            fontsize=8.5 * SF,
            color=META_INK,
            linespacing=1.6,
            va="top",
            zorder=6.0
        )

        bar_x0 = 0.05
        bar_y0 = 0.770
        bar_w = 0.22
        bar_h = 0.012
        num_steps = 5
        step_w = bar_w / num_steps

        ax.text(
            bar_x0, bar_y0 + 0.018,
            "DEPTH - METERS (FEET)",
            transform=ax.transAxes,
            fontfamily="serif",
            fontsize=7.5 * SF,
            fontweight="bold",
            color=MAIN_INK,
            va="bottom",
            zorder=6.0
        )

        for i in range(num_steps):
            seg_color = cmap((i + 1) / (num_steps + 1))
            rect = mpatches.Rectangle(
                (bar_x0 + i * step_w, bar_y0), step_w, bar_h,
                transform=ax.transAxes,
                facecolor=seg_color,
                edgecolor=MAIN_INK,
                linewidth=0.5 * SF,
                zorder=6.0
            )
            ax.add_patch(rect)

        depth_labels = ["0m\n(0')", "3m\n(10')", "6m\n(20')", "9m\n(30')", "12m\n(39')", "15m\n(49')"]
        for i, lbl in enumerate(depth_labels):
            ax.text(
                bar_x0 + i * step_w, bar_y0 - 0.007,
                lbl,
                transform=ax.transAxes,
                fontfamily="serif",
                fontsize=6.5 * SF,
                color=META_INK,
                ha="center",
                va="top",
                linespacing=1.1,
                zorder=6.0
            )

        num_sb_segments = 4
        seg_w = sb_w / num_sb_segments

        scale_halo = mpatches.Rectangle(
            (sb_x0 - 0.015, sb_y0 - 0.022), sb_w + 0.03, 0.065,
            transform=ax.transAxes,
            facecolor=LAND_BG,
            edgecolor="none",
            zorder=5.9
        )
        ax.add_patch(scale_halo)

        ax.text(
            sb_x0, sb_y0 + 0.018,
            "SCALE  1 : 12,000",
            transform=ax.transAxes,
            fontfamily="serif",
            fontsize=7.5 * SF,
            fontweight="bold",
            color=MAIN_INK,
            va="bottom",
            zorder=6.0
        )

        for i in range(num_sb_segments):
            fc = MAIN_INK if i % 2 == 0 else LAND_BG
            rect = mpatches.Rectangle(
                (sb_x0 + i * seg_w, sb_y0), seg_w, sb_h,
                transform=ax.transAxes,
                facecolor=fc,
                edgecolor=MAIN_INK,
                linewidth=0.6 * SF,
                zorder=6.0
            )
            ax.add_patch(rect)

        ax.text(sb_x0, sb_y0 - 0.007, "0", transform=ax.transAxes, fontfamily="serif", fontsize=6.5 * SF, color=META_INK, ha="center", va="top", zorder=6.0)
        ax.text(sb_x0 + sb_w * 0.5, sb_y0 - 0.007, "250 m", transform=ax.transAxes, fontfamily="serif", fontsize=6.5 * SF, color=META_INK, ha="center", va="top", zorder=6.0)
        ax.text(sb_x0 + sb_w, sb_y0 - 0.007, "500 m (1,640 ft)", transform=ax.transAxes, fontfamily="serif", fontsize=6.5 * SF, color=META_INK, ha="center", va="top", zorder=6.0)

        ax.set_xlim(WEST, EAST)
        ax.set_ylim(SOUTH, NORTH)
        ax.set_aspect(aspect_correction)
        ax.axis("off")

        frame_outer = mpatches.Rectangle((0.02, 0.02), 0.96, 0.96, transform=fig.transFigure,
                                         fill=False, edgecolor=MAIN_INK, linewidth=1.8 * SF)
        frame_inner = mpatches.Rectangle((0.025, 0.025), 0.95, 0.95, transform=fig.transFigure,
                                         fill=False, edgecolor=MAIN_INK, linewidth=0.6 * SF)
        fig.patches.extend([frame_outer, frame_inner])

        file_prefix = f"lac_dufresne_{POSTER_SIZE.lower()}_{palette_name.lower()}"
        png_path = OPTIONS_DIR / f"{file_prefix}.png"
        pdf_path = OPTIONS_DIR / f"{file_prefix}.pdf"

        plt.savefig(png_path, dpi=300, facecolor=LAND_BG, edgecolor="none")
        plt.savefig(pdf_path, facecolor=LAND_BG, edgecolor="none")
        plt.close(fig)  

    print(f"Finished! All 5 palette outputs saved to: {OPTIONS_DIR.resolve()}")

else:
    # Transparent black fallback mode
    LINE_COLOR = "#000000"
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor="none")
    ax.set_facecolor("none")

    # Warning Fix: List comprehension applied directly to underlying Shapely geometries
    clean_depth_gdf = depth_gdf[[g.length >= MIN_CONTOUR_LENGTH if g else False for g in depth_gdf.geometry]]
    clean_depth_gdf.plot(
        ax=ax,
        color=LINE_COLOR,
        linewidth=0.6 * SF,
        linestyle="--",
        aspect="auto",
        zorder=1
    )

    if not pit_gdf.empty:
        pit_gdf.plot(
            ax=ax,
            color=LINE_COLOR,
            marker="+",
            markersize=60 * SF,
            linewidth=1.2 * SF,
            aspect="auto",
            zorder=1.5
        )

    lake_gdf.boundary.plot(
        ax=ax,
        color=LINE_COLOR,
        linewidth=1.4 * SF,
        aspect="auto",
        zorder=2
    )

    if clipped_stream_lines:
        ax.add_collection(LineCollection(clipped_stream_lines, colors=LINE_COLOR, linewidths=0.8 * SF, zorder=2.4))

    ax.scatter([CABIN_COORDS[0]], [CABIN_COORDS[1]], s=60 * SF, marker="s", color=LINE_COLOR, zorder=2.8)

    if local_lines:
        ax.add_collection(LineCollection(local_lines, colors=LINE_COLOR, linewidths=1.0 * SF, zorder=3))
    if secondary_lines:
        ax.add_collection(LineCollection(secondary_lines, colors=LINE_COLOR, linewidths=1.6 * SF, zorder=4))
    if primary_lines:
        ax.add_collection(LineCollection(primary_lines, colors=LINE_COLOR, linewidths=2.2 * SF, zorder=5))

    ax.set_xlim(WEST, EAST)
    ax.set_ylim(SOUTH, NORTH)
    ax.set_aspect(aspect_correction)
    plt.axis("off")
    plt.tight_layout(pad=0)

    output_path = OPTIONS_DIR / f"lac_dufresne_{POSTER_SIZE.lower()}_transparent_black.png"
    plt.savefig(
        output_path,
        dpi=300,
        transparent=True,
        facecolor="none",
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0
    )
    plt.close(fig)
    print(f"Finished! Output saved to: {output_path.resolve()}")