"""Metric catalog / detail / write endpoints + the live DSL parse preview."""
from fastapi import Request
from sqlalchemy.orm import Session

from app.algorithms.dsl_parser import parse_dsl
from app.middlewares import audit_logger
from app.middlewares.quota import quota_snapshot
from app.models import User
from app.schemas.metric import MetricCreate, MetricUpdate
from app.services import metric_service
from app.utils.pagination import page_args


def list_metrics(
    db: Session,
    q: str | None = None,
    domain: str | None = None,
    status: str | None = None,
    team_id: int | None = None,
    page: int | None = 1,
    page_size: int | None = 50,
) -> dict:
    current_page, current_size = page_args(page, page_size)
    return metric_service.list_metrics(db, q, domain, status, team_id, current_page, current_size)


def get_metric(db: Session, metric_id: int) -> dict:
    return metric_service.get_metric_detail(db, metric_id)


def create_metric(request: Request, db: Session, user: User, payload: MetricCreate) -> dict:
    metric = metric_service.create_metric(db, user, payload)
    audit_logger.record(
        request,
        "METRIC_CREATED",
        "metric",
        metric.id,
        after={"metric_key": metric.metric_key, "domain": metric.domain, "status": metric.status},
    )
    return metric_service.get_metric_detail(db, metric.id)


def update_metric(request: Request, db: Session, user: User, metric_id: int, payload: MetricUpdate) -> dict:
    metric = metric_service.get_metric_or_404(db, metric_id)
    before = {
        "display_name": metric.display_name,
        "status": metric.status,
        "description": metric.description,
        "consumers": metric.consumers_json,
    }
    metric = metric_service.update_metric(db, user, metric, payload)
    audit_logger.record(
        request,
        "METRIC_UPDATED",
        "metric",
        metric.id,
        before=before,
        after={
            "display_name": metric.display_name,
            "status": metric.status,
            "description": metric.description,
            "consumers": metric.consumers_json,
        },
    )
    return metric_service.get_metric_detail(db, metric.id)


def parse_dsl_preview(payload) -> dict:
    parsed = parse_dsl(payload.dsl_text)
    return parsed


def quota(db: Session, user: User) -> dict:
    return quota_snapshot(user)
