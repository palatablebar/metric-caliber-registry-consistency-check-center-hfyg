"""Liveness probe used by the compose healthcheck and by QA smoke tests."""
from fastapi import APIRouter

from app.config.settings import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "metricd-backend", "seed_demo": settings.SEED_DEMO}
