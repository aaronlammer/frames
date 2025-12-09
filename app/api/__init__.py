"""
API routes
"""
from fastapi import APIRouter
from app.api import frames

router = APIRouter()

# Include frames routes
router.include_router(frames.router, prefix="/frames", tags=["frames"])
