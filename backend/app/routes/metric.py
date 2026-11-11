from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import metric_controller, version_controller
from app.middlewares.auth import get_current_user
from app.middlewares.rbac import require_roles
from app.models import User
from app.schemas.metric import DslParseRequest, MetricCreate, MetricUpdate, VersionCreate, VersionUpdate

router = APIRouter(tags=["metrics"])

WRITER = require_roles("admin", "owner")


@router.get("/metrics")
def list_metrics(
    q: str | None = None,
    domain: str | None = None,
    status: str | None = None,
    team_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return metric_controller.list_metrics(db, q, domain, status, team_id, page, page_size)


@router.get("/metrics/{metric_id}")
def get_metric(metric_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return metric_controller.get_metric(db, metric_id)


@router.post("/metrics")
def create_metric(
    request: Request,
    payload: MetricCreate,
    db: Session = Depends(get_db),
    user: User = Depends(WRITER),
):
    return metric_controller.create_metric(request, db, user, payload)


@router.patch("/metrics/{metric_id}")
def update_metric(
    request: Request,
    metric_id: int,
    payload: MetricUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(WRITER),
):
    return metric_controller.update_metric(request, db, user, metric_id, payload)


@router.get("/metrics/{metric_id}/versions")
def list_versions(metric_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return version_controller.list_versions(db, metric_id)


@router.post("/metrics/{metric_id}/versions")
def create_version(
    request: Request,
    metric_id: int,
    payload: VersionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(WRITER),
):
    return version_controller.create_version(request, db, user, metric_id, payload)


@router.get("/metrics/{metric_id}/compare")
def compare_versions(
    metric_id: int,
    version_a: int,
    version_b: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return version_controller.compare(db, metric_id, version_a, version_b)


@router.patch("/versions/{version_id}")
def update_version(
    request: Request,
    version_id: int,
    payload: VersionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(WRITER),
):
    return version_controller.update_version(request, db, user, version_id, payload)


@router.post("/dsl/parse")
def parse_dsl(payload: DslParseRequest, _user: User = Depends(get_current_user)):
    return metric_controller.parse_dsl_preview(payload)


@router.get("/quota")
def quota(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return metric_controller.quota(db, user)
