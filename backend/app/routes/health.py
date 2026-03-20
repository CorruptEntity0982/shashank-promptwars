"""
Health check endpoints for monitoring service status
"""
from fastapi import APIRouter

from app.services.bigquery_service import bigquery_service
from app.services.pubsub_service import pubsub_service

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


@router.get("/gcp")
async def gcp_health_check():
    """Check connectivity for integrated Google Cloud services."""
    bq_ok, bq_msg = bigquery_service.health_check()
    pubsub_ok, pubsub_msg = pubsub_service.health_check()

    overall = "ok" if bq_ok and pubsub_ok else "degraded"
    return {
        "status": overall,
        "services": {
            "bigquery": {
                "connected": bq_ok,
                "detail": bq_msg,
            },
            "pubsub": {
                "connected": pubsub_ok,
                "detail": pubsub_msg,
            },
        },
    }
