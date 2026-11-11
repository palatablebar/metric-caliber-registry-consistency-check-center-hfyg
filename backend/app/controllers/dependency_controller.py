"""Dependency graph and impact closure projections."""
from sqlalchemy.orm import Session

from app.services import dependency_service


def graph(db: Session) -> dict:
    return dependency_service.graph_payload(db)


def impact(db: Session, metric_id: int) -> dict:
    return dependency_service.impact_payload(db, metric_id)
