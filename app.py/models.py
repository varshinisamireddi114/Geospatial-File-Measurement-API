from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FileMetadata(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: str
    status: str

class MeasurementItem(BaseModel):
    feature_id: int
    geometry_type: str
    area_sq_meters: Optional[float] = None
    length_meters: Optional[float] = None
    properties: Dict[str, Any]
    error: Optional[str] = None

class FileMeasurementResponse(BaseModel):
    id: str
    filename: str
    unit: str = "metric (meters / sq meters)"
    measurements: List[MeasurementItem]