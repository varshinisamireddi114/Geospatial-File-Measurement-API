import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "storage"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)