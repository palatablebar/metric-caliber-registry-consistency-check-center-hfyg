"""Recent audit trail projection for the governance console."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog
from app.utils.formatters import iso


def serialize_audit(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "actor_id": log.actor_id,
        "actor_email": log.actor_email,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "before": log.before_json,
        "after": log.after_json,
        "ip": log.ip,
        "created_at": iso(log.created_at),
    }


def recent(db: Session, limit: int = 30) -> list[dict]:
    logs = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return [serialize_audit(log) for log in logs]
