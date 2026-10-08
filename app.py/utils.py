import geopandas as gpd
import fiona
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString, Point
from pyproj import CRS

# Enable KML support in fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

def get_projected_crs(gdf: gpd.GeoDataFrame) -> CRS:
    """
    Selects an appropriate projected coordinate system (UTM zone) 
    based on the centroid of the geometries in EPSG:4326.
    """
    # Ensure standard geographic CRS for centroid estimation
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    
    gdf_wgs84 = gdf.to_crs(epsg=4326)
    centroid = gdf_wgs84.unary_union.centroid
    lon, lat = centroid.x, centroid.y
    
    # Estimate UTM zone CRS based on coordinates
    utm_zone = int((lon + 180) / 6) + 1
    hemisphere = "north" if lat >= 0 else "south"
    return CRS.from_string(f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

def process_geospatial_file(file_path: str):
    """
    Reads Shapefile (.zip) or .kml, transforms CRS, and computes measurements.
    """
    gdf = gpd.read_file(file_path)
    
    if gdf.crs is None:
        # Default fallback to EPSG:4326 if not specified in file
        gdf = gdf.set_crs(epsg=4326)
        
    original_crs = str(gdf.crs)
    
    # Project to metric-based CRS (UTM) for accurate measurement calculations
    projected_crs = get_projected_crs(gdf)
    gdf_projected = gdf.to_crs(projected_crs)
    
    measurements = []
    
    for idx, row in gdf_projected.iterrows():
        geom = row.geometry
        props = {k: v for k, v in row.items() if k != 'geometry' and not isinstance(v, (gpd.GeoSeries, gpd.GeoDataFrame))}
        
        # Clean non-serializable properties
        props = {k: (str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v) for k, v in props.items()}

        item = {
            "feature_id": int(idx),
            "geometry_type": geom.geom_type if geom else "None",
            "properties": props,
            "area_sq_meters": None,
            "length_meters": None,
            "error": None
        }

        if geom is None or geom.is_empty:
            item["error"] = "Empty or null geometry"
            measurements.append(item)
            continue

        # Handle Polygon / MultiPolygon
        if isinstance(geom, (Polygon, MultiPolygon)):
            item["area_sq_meters"] = round(float(geom.area), 2)
            item["length_meters"] = round(float(geom.length), 2)  # Perimeter
            
        # Handle LineString / MultiLineString
        elif isinstance(geom, (LineString, MultiLineString)):
            item["length_meters"] = round(float(geom.length), 2)
            
        # Handle Point / MultiPoint
        elif isinstance(geom, Point):
            pass  # No measurement needed for points
            
        else:
            item["error"] = f"Unsupported geometry type: {geom.geom_type}"

        measurements.append(item)

    return len(gdf), original_crs, measurements