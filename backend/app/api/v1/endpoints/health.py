from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.health import Health

router = APIRouter()


@router.get("/health", response_model=Health)
def get_health(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Health:
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        database_status = "unavailable"

    return Health(
        status="ok",
        version=settings.APP_VERSION,
        dependencies={"database": database_status},
    )
