"""Consistency check batches, finding triage and the CSV impact download."""
from fastapi import Request
from sqlalchemy.orm import Session

from app.constants.finding_status import FindingStatus
from app.middlewares import audit_logger
from app.models import User
from app.schemas.check import CheckCreate, FindingTriageRequest
from app.services import check_service
from app.utils.pagination import page_args


def list_checks(db: Session, page: int | None = 1, page_size: int | None = 10) -> dict:
    current_page, current_size = page_args(page, page_size)
    return check_service.list_checks(db, current_page, current_size)


def create_check(request: Request, db: Session, user: User, payload: CheckCreate) -> dict:
    check = check_service.create_check(db, user, payload.scope)
    audit_logger.record(
        request,
        "CHECK_CREATED",
        "consistency_check",
        check["id"],
        after={"batch_no": check["batch_no"], "scope": check["scope"]},
    )
    return check


def latest_check(db: Session) -> dict:
    check = check_service.get_latest_check(db)
    if check is None:
        return {"check": None, "findings": []}
    return check_service.check_detail(db, check.id, include_findings=True)


def check_detail(db: Session, check_id: int) -> dict:
    return check_service.check_detail(db, check_id, include_findings=True)


def triage_finding(request: Request, db: Session, user: User, finding_id: int, payload: FindingTriageRequest) -> dict:
    from app.constants.error_codes import AppError, ErrorCode
    from app.models import ConflictFinding

    finding = db.get(ConflictFinding, finding_id)
    if finding is None:
        raise AppError(ErrorCode.FINDING_NOT_FOUND, detail={"finding_id": finding_id})
    before = finding.status
    finding = check_service.triage_finding(db, finding, payload.status)
    audit_logger.record(
        request,
        "FINDING_TRIAGED",
        "conflict_finding",
        finding.id,
        before={"status": before},
        after={"status": finding.status},
    )
    return {"finding": check_service.serialize_finding(finding), "status": finding.status}


def impact_csv(db: Session, check_id: int):
    from fastapi.responses import Response

    filename, content = check_service.impact_csv(db, check_id)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
