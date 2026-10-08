# Geospatial File Measurement API

A production-grade REST API built with **FastAPI** and **GeoPandas** that processes uploaded geospatial vector files (`.zip` Shapefiles or `.kml`), handles CRS coordinate transformations, and returns spatial measurements (area and length).

---

## Technical Stack
- **Framework**: FastAPI (Python 3.10+)
- **Geospatial Processing**: GeoPandas, Shapely, PyPROJ, Fiona
- **Data Validation**: Pydantic v2
- **Server**: Uvicorn

---

## Setup & Running Locally

### Prerequisites
Ensure `GDAL` binary dependencies are installed on your system if running outside a container.

### Installation Steps



1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access Interactive API Docs:**
   Open your browser at `http://127.0.0.1:8000/docs`

---

## API Documentation

### 1. Upload & Process File
* **Endpoint**: `POST /api/files/`
* **Content-Type**: `multipart/form-data`
* **Payload**: `file` (`.zip` Shapefile or `.kml`)
* **Response (201 Created)**:
  ```json
  {
    "id": "a1b2c3d4",
    "filename": "survey.kml",
    "feature_count": 12,
    "crs": "EPSG:4326",
    "status": "COMPLETED"
  }
  ```

### 2. Get File Information
* **Endpoint**: `GET /api/files/{id}/`
* **Response (200 OK)**:
  ```json
  {
    "id": "a1b2c3d4",
    "filename": "survey.kml",
    "feature_count": 12,
    "crs": "EPSG:4326",
    "status": "COMPLETED"
  }
  ```

### 3. Get File Measurements
* **Endpoint**: `GET /api/files/{id}/measurements/`
* **Response (200 OK)**:
  ```json
  {
    "id": "a1b2c3d4",
    "filename": "survey.kml",
    "unit": "metric (meters / sq meters)",
    "measurements": [
      {
        "feature_id": 0,
        "geometry_type": "Polygon",
        "area_sq_meters": 145020.5,
        "length_meters": 1540.2,
        "properties": { "Name": "Zone A" },
        "error": null
      },
      {
        "feature_id": 1,
        "geometry_type": "Point",
        "area_sq_meters": null,
        "length_meters": null,
        "properties": { "Name": "Beacon 1" },
        "error": null
      }
    ]
  }
  ```

---

## Architecture & Flow

### 1. File Upload & Ingestion
When a file is uploaded via `POST /api/files/`, validation checks for allowed file extensions (`.zip` or `.kml`). Files are saved temporarily to local disk storage before driver execution.

### 2. File Processing
`GeoPandas` (backed by `Fiona`) reads vector layers. Fiona drivers are explicitly configured to support KML parsing alongside standard ESRI Shapefiles.

### 3. CRS Handling & Transformation
* **Problem**: Geographic coordinate systems like `EPSG:4326` use angular degrees (latitude/longitude), making direct planar area/distance calculations mathematically incorrect.
* **Solution**: The application extracts the feature collection's geographic centroid. Based on the longitude and latitude, it dynamically calculates the local **UTM (Universal Transverse Mercator) zone** projected coordinate system (e.g., `EPSG:32644`). The geometries are reprojected using PyPROJ (`gdf.to_crs(...)`) prior to metric calculation.

### 4. Measurement Calculation
* **Polygons / MultiPolygons**: Calculate metric area ($m^2$) and perimeter length ($m$).
* **LineStrings / MultiLineStrings**: Calculate line length ($m$).
* **Points**: Skipped gracefully (no measurements assigned).
* **Unsupported / Invalid Geometries**: Trapped safely per-feature with error strings attached to prevent complete API request crashes.

---

## Design Decisions

1. **FastAPI over Django**: Selected for high-performance asynchronous execution, explicit schema generation via Pydantic, and lightweight setup.
2. **Dynamic UTM CRS Selection**: Chosen over fixed planar projections (e.g., Web Mercator EPSG:3857) because Web Mercator introduces significant area distortion away from the equator. Localized UTM zones preserve shape and local distance accuracy.
3. **In-Memory Result Caching**: Utilized dict-based caching for low overhead; easily drop-in replaceable with PostgreSQL/PostGIS or Redis for production scale.

---

## Key Learnings & Future Scope

### Key Learnings
* Handling GIS drivers across driver implementations (e.g., enabling `LIBKML` drivers in Fiona).
* Mathematical distortion issues associated with calculating geodesic geometries over geographic coordinate systems vs. projected systems.

### Future Scope
* **PostGIS Storage**: Persist features using GeoAlchemy2 and PostgreSQL for spatial querying capabilities.
* **Celery Async Task Queue**: Process large multi-gigabyte spatial datasets asynchronously in the background.
* **GeoJSON Support**: Expand supported formats to include `.geojson` and `.gpkg` (GeoPackage).