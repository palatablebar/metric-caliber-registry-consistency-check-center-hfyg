"""Owner teams (4 domain teams of 微光课堂)."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants.domains import DOMAIN_LABELS
from app.constants.error_codes import AppError, ErrorCode
from app.models import MetricDefinition, OwnerTeam
from app.utils.formatters import iso


def serialize_team(team: OwnerTeam, metric_count: int = 0) -> dict:
    return {
        "id": team.id,
        "code": team.code,
        "name": team.name,
        "domain": team.domain,
        "domain_label": DOMAIN_LABELS.get(team.domain, team.domain),
        "lead_name": team.lead_name,
        "member_count": team.member_count,
        "sla_hours": team.sla_hours,
        "metric_count": metric_count,
        "created_at": iso(team.created_at),
    }


def list_teams(db: Session) -> list[dict]:
    counts = dict(
        db.execute(
            select(MetricDefinition.owner_team_id, func.count(MetricDefinition.id)).group_by(
                MetricDefinition.owner_team_id
            )
        ).all()
    )
    teams = db.scalars(select(OwnerTeam).order_by(OwnerTeam.id)).all()
    return [serialize_team(team, int(counts.get(team.id, 0))) for team in teams]


def get_team_or_404(db: Session, team_id: int) -> OwnerTeam:
    team = db.get(OwnerTeam, team_id)
    if team is None:
        raise AppError(ErrorCode.TEAM_NOT_FOUND, detail={"team_id": team_id})
    return team


def find_team_by_code(db: Session, code: str) -> OwnerTeam | None:
    return db.scalar(select(OwnerTeam).where(OwnerTeam.code == code))
