from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import team_controller
from app.middlewares.auth import get_current_user
from app.models import User

router = APIRouter(tags=["teams"])


@router.get("/teams")
def list_teams(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return team_controller.list_teams(db)
