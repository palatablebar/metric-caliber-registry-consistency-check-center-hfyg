"""Audit trail endpoint (governance committee view)."""
from sqlalchemy.orm import Session

from app.services import audit_service


def recent(db: Session, limit: int = 30) -> dict:
    return {"items": audit_service.recent(db, limit)}
