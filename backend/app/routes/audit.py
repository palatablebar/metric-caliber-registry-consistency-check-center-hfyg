from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import audit_controller
from app.middlewares.auth import get_current_user
from app.models import User

router = APIRouter(tags=["audit"])


@router.get("/audit/recent")
def recent(
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return audit_controller.recent(db, limit)
