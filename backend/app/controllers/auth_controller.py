"""Auth endpoints: login issues the JWT, /me restores the session."""
from fastapi import Request
from sqlalchemy.orm import Session

from app.middlewares import audit_logger
from app.models import User
from app.services import auth_service
from app.utils.jwt import create_access_token
from app.utils.logger import log_event


def login(request: Request, payload, db: Session) -> dict:
    try:
        user = auth_service.authenticate(db, payload.email, payload.password)
    except Exception:
        log_event("LOGIN_FAILED", email=payload.email, reason="bad_credentials")
        raise
    request.state.user_claims = {"sub": str(user.id), "email": user.email, "role": user.role}
    audit_logger.record(request, "LOGIN", "user", user.id, after={"email": user.email, "role": user.role})
    log_event("LOGIN_SUCCEEDED", email=user.email, role=user.role)
    return {"token": create_access_token(user), "user": auth_service.serialize_user(db, user)}


def me(db: Session, user: User) -> dict:
    return {"user": auth_service.serialize_user(db, user)}
