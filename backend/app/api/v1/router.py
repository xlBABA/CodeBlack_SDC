from fastapi import APIRouter

from app.api.v1.endpoints import careers, health, profile, scenarios, trends

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(careers.router, tags=["careers"])
api_router.include_router(trends.router, tags=["trends"])
api_router.include_router(scenarios.router, tags=["scenarios"])
