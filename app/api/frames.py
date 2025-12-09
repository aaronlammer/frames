"""
Frames API endpoint
"""
import os
import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/{movie}")
async def get_frames(movie: str):
    """
    Return the frames manifest for a specific movie
    """
    manifest_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'static', 'frames', movie, 'manifest.json'
    )
    
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        return manifest
    
    return {"frames": [], "movie_name": None, "total_frames": 0}
