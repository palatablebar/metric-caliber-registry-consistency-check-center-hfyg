from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import check_controller
from app.middlewares.auth import get_current_user
from app.middlewares.rbac import require_roles
from app.models import User
from app.schemas.check import CheckCreate, FindingTriageRequest

router = APIRouter(tags=["checks"])


@router.get("/checks")
def list_checks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return check_controller.list_checks(db, page, page_size)


@router.get("/checks/latest")
def latest_check(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return check_controller.latest_check(db)


@router.post("/checks")
def create_check(
    request: Request,
    payload: CheckCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # any authenticated role may trigger a check batch (it is analysis, not data mutation)
    return check_controller.create_check(request, db, user, payload)


@router.get("/checks/{check_id}")
def check_detail(check_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return check_controller.check_detail(db, check_id)


@router.get("/checks/{check_id}/impact.csv")
def impact_csv(check_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return check_controller.impact_csv(db, check_id)


@router.patch("/findings/{finding_id}")
def triage_finding(
    request: Request,
    finding_id: int,
    payload: FindingTriageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    return check_controller.triage_finding(request, db, user, finding_id, payload)
