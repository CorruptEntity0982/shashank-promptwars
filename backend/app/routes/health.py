"""
Health check endpoints for monitoring service status
"""
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Health check endpoint
    Returns service status
    """
    return {
        "status": "ok",
        "service": "backend",
    }
