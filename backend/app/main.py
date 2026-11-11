"""metricd API entrypoint — 指标口径注册与一致性检查中心.

Middleware order (outermost first):
    CORS -> RequestId -> Auth -> RateLimit -> Audit -> routes -> error handlers
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.database import init_db
from app.config.settings import settings
from app.middlewares.audit_logger import AuditMiddleware
from app.middlewares.auth import AuthMiddleware
from app.middlewares.error_handler import RequestIdMiddleware, install_error_handlers
from app.middlewares.quota import RateLimitMiddleware
from app.routes import audit, auth, check, dependency, health, metric, team
from app.utils.logger import log_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs(settings.ARTIFACT_DIR, exist_ok=True)
    if settings.SEED_DEMO:
        try:
            from scripts.seed_demo import run_seed

            result = run_seed()
            log_event(
                "SEED_DEMO_FINISHED",
                teams=result.get("owner_team"),
                metrics=result.get("metric_definition"),
                versions=result.get("metric_version"),
                check="seed",
            )
        except Exception as exc:  # seed must never block startup
            log_event("SEED_DEMO_FAILED", error=f"{type(exc).__name__}: {exc}")
    yield


app = FastAPI(
    title="metricd API",
    description="微光课堂指标口径注册与一致性检查中心",
    version="1.0.0",
    lifespan=lifespan,
)

install_error_handlers(app)

app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
app.include_router(metric.router, prefix="/api")
app.include_router(dependency.router, prefix="/api")
app.include_router(check.router, prefix="/api")
app.include_router(team.router, prefix="/api")
app.include_router(audit.router, prefix="/api")


@app.get("/api")
def api_index() -> dict:
    return index()


@app.get("/")
def index() -> dict:
    return {
        "service": "metricd-backend",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/auth/login",
            "/metrics",
            "/metrics/{id}",
            "/metrics/{id}/versions",
            "/metrics/{id}/compare",
            "/dsl/parse",
            "/dependencies/graph",
            "/metrics/{id}/impact",
            "/checks",
            "/checks/latest",
            "/checks/{id}/impact.csv",
            "/teams",
            "/audit/recent",
        ],
    }
