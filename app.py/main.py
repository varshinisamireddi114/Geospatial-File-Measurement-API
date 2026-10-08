from fastapi import FastAPI
from app.routers import files

app = FastAPI(
    title="Geospatial File Measurement API",
    description="API for parsing Shapefiles and KML files to calculate area and length measurements.",
    version="1.0.0"
)

app.include_router(files.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Geospatial Measurement API"}