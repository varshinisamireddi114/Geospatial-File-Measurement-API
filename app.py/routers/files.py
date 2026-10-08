import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.config import UPLOAD_DIR
from app.models import FileMetadata, FileMeasurementResponse
from app.utils import process_geospatial_file

router = APIRouter(prefix="/api/files", tags=["Files"])

# Simple in-memory database store
db_files = {}
db_measurements = {}

@router.post("/", response_model=FileMetadata, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    if not (filename.endswith(".zip") or filename.endswith(".kml")):
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Please upload a .zip (Shapefile) or .kml file."
        )

    file_id = str(uuid.uuid4())[:8]
    saved_file_path = UPLOAD_DIR / f"{file_id}_{filename}"

    # Save uploaded file to local disk
    with saved_file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        feature_count, crs, measurements = process_geospatial_file(str(saved_file_path))
        
        file_meta = FileMetadata(
            id=file_id,
            filename=filename,
            feature_count=feature_count,
            crs=crs,
            status="COMPLETED"
        )
        
        # Save to in-memory store
        db_files[file_id] = file_meta
        db_measurements[file_id] = measurements
        
        return file_meta

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process geospatial file: {str(e)}")

@router.get("/{file_id}/", response_model=FileMetadata)
async def get_file_info(file_id: str):
    if file_id not in db_files:
        raise HTTPException(status_code=404, detail="File ID not found")
    return db_files[file_id]

@router.get("/{file_id}/measurements/", response_model=FileMeasurementResponse)
async def get_file_measurements(file_id: str):
    if file_id not in db_files:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    return FileMeasurementResponse(
        id=file_id,
        filename=db_files[file_id].filename,
        measurements=db_measurements[file_id]
    )