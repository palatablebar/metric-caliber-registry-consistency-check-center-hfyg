"""Authentication + quota reset helpers."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.error_codes import AppError, ErrorCode
from app.constants.roles import ROLE_LABELS, Role
from app.models import OwnerTeam, User
from app.utils.password import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower().strip()))


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        # same message for unknown user and wrong password
        raise AppError(ErrorCode.UNAUTHORIZED, message="邮箱或密码不正确")
    reset_daily_quota_if_needed(db, user)
    return user


def reset_daily_quota_if_needed(db: Session, user: User) -> None:
    today = date.today()
    if user.quota_used_date != today:
        user.quota_used_date = today
        user.quota_used = 0
        db.commit()


def serialize_user(db: Session, user: User) -> dict:
    team = db.get(OwnerTeam, user.team_id) if user.team_id else None
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "role_label": ROLE_LABELS.get(user.role, user.role),
        "team_id": user.team_id,
        "team_code": team.code if team else None,
        "team_name": team.name if team else None,
        "daily_check_quota": user.daily_check_quota,
        "quota_used": user.quota_used,
    }


def ensure_demo_user(db: Session, email: str, display_name: str, role: str, password: str, team_id=None) -> User:
    """Idempotent natural-key upsert used by the seed (never overwrites a changed password)."""
    user = get_user_by_email(db, email)
    if user is None:
        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name=display_name,
            role=role,
            team_id=team_id,
            daily_check_quota=40,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    user.display_name = display_name
    user.role = role
    if team_id is not None:
        user.team_id = team_id
    db.commit()
    return user


__all__ = [
    "Role",
    "get_user_by_email",
    "authenticate",
    "reset_daily_quota_if_needed",
    "serialize_user",
    "ensure_demo_user",
]
