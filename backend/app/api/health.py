"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.get("/healthz")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {
            "ok": True,
            "status": "healthy",
            "service": "getgsa-api",
            "database": "connected"
        }
    except Exception as e:
        return {
            "ok": False,
            "status": "unhealthy",
            "service": "getgsa-api",
            "database": "disconnected",
            "error": str(e)
        }
