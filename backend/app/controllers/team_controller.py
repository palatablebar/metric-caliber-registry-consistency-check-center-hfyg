"""Owner team listing."""
from sqlalchemy.orm import Session

from app.services import team_service


def list_teams(db: Session) -> dict:
    return {"items": team_service.list_teams(db)}
