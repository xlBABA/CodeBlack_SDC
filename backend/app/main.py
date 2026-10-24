from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.db import models  # noqa: F401  (registers ORM tables on Base.metadata)
from app.db.session import Base, engine
from app.spa import mount_spa

settings = get_settings()

# repo_root/frontend/dist, sibling to this repo_root/backend checkout.
# Built separately (`npm run build` in frontend/) — never built here.
FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev-stage schema bootstrap: creates missing tables only, never drops or
    # resets existing data. Migrating to Postgres replaces this with Alembic
    # migrations (see backend README / Milestone 2 report for the plan).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
mount_spa(app, FRONTEND_DIST_DIR)
