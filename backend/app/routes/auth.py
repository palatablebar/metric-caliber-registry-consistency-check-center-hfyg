from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import auth_controller
from app.middlewares.auth import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    return auth_controller.login(request, payload, db)


@router.get("/me")
def me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return auth_controller.me(db, user)
