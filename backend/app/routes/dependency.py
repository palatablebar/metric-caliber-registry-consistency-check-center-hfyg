from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import dependency_controller
from app.middlewares.auth import get_current_user
from app.models import User

router = APIRouter(tags=["dependencies"])


@router.get("/dependencies/graph")
def graph(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return dependency_controller.graph(db)


@router.get("/metrics/{metric_id}/impact")
def impact(metric_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return dependency_controller.impact(db, metric_id)
