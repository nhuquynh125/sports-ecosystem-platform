from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness and database readiness")
def health(db: DbSession):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ok", "database": "up", "version": settings.VERSION}
