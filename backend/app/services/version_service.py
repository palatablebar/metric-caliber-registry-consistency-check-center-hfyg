"""Metric versions: history, DSL write path (parse → five-tuple → persist) and
dependency synchronisation for the ``using (...)`` clause."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.algorithms.dsl_parser import parse_or_raise
from app.constants.error_codes import AppError, ErrorCode
from app.constants.roles import Role
from app.middlewares.rbac import assert_can_edit_metric
from app.models import MetricDefinition, MetricDependency, MetricVersion, OwnerTeam, User
from app.services.metric_service import get_metric_or_404, serialize_version
from app.utils.formatters import iso
from app.utils.logger import log_event


def _team_map(db: Session) -> dict[int, OwnerTeam]:
    return {team.id: team for team in db.scalars(select(OwnerTeam)).all()}


def list_versions(db: Session, metric_id: int) -> list[dict]:
    metric = get_metric_or_404(db, metric_id)
    versions = db.scalars(
        select(MetricVersion).where(MetricVersion.metric_id == metric.id).order_by(MetricVersion.version_no)
    ).all()
    teams = _team_map(db)
    return [serialize_version(version, teams.get(version.team_id)) for version in versions]


def get_version_or_404(db: Session, version_id: int) -> MetricVersion:
    version = db.get(MetricVersion, version_id)
    if version is None:
        raise AppError(ErrorCode.VERSION_NOT_FOUND, detail={"version_id": version_id})
    return version


def _apply_parsed_tuple(version: MetricVersion, parsed: dict) -> None:
    version.agg = parsed["agg"]
    version.measure = parsed["measure"]
    version.source_table = parsed["source_table"]
    version.filters_json = parsed["filters"]
    version.window = parsed["window"]
    version.grain = parsed["grain"]
    version.parse_status = "ok"
    version.parse_error = None


def _sync_dsl_dependencies(db: Session, metric: MetricDefinition, dependency_keys: list[str]) -> None:
    """Upsert metric→metric edges declared by the DSL `using (...)` clause."""
    for key in dependency_keys:
        target = db.scalar(select(MetricDefinition).where(MetricDefinition.metric_key == key))
        if target is None:
            raise AppError(
                ErrorCode.DSL_SEMANTIC,
                message=f"using 中引用的指标 `{key}` 不存在",
                detail={"missing_metric": key},
            )
        exists = db.scalar(
            select(MetricDependency).where(
                MetricDependency.from_metric_id == metric.id,
                MetricDependency.to_metric_id == target.id,
            )
        )
        if exists is None:
            db.add(
                MetricDependency(
                    from_metric_id=metric.id,
                    to_metric_id=target.id,
                    relation="dsl",
                    note="由 DSL using 子句维护",
                )
            )


def create_version(db: Session, user: User, metric_id: int, payload) -> MetricVersion:
    metric = get_metric_or_404(db, metric_id)
    assert_can_edit_metric(user, metric)
    parsed = parse_or_raise(payload.dsl_text)

    if user.role == Role.OWNER.value:
        if payload.team_id is not None and payload.team_id != user.team_id:
            raise AppError(
                ErrorCode.FORBIDDEN,
                message="只能以本团队名义提交指标版本",
                detail={"user_team_id": user.team_id, "requested_team_id": payload.team_id},
            )
        team_id = payload.team_id or user.team_id
    else:
        team_id = payload.team_id or metric.owner_team_id
    if team_id is None or db.get(OwnerTeam, team_id) is None:
        raise AppError(ErrorCode.TEAM_NOT_FOUND, detail={"team_id": team_id})

    next_no = int(
        db.scalar(select(func.max(MetricVersion.version_no)).where(MetricVersion.metric_id == metric.id)) or 0
    ) + 1
    version = MetricVersion(
        metric_id=metric.id,
        team_id=team_id,
        version_no=next_no,
        dsl_text=payload.dsl_text.strip(),
        is_current=bool(payload.set_current),
        created_by=user.display_name or user.email,
    )
    _apply_parsed_tuple(version, parsed)
    if payload.effective_from:
        try:
            version.effective_from = date.fromisoformat(payload.effective_from)
        except ValueError as exc:
            raise AppError(ErrorCode.DSL_SEMANTIC, message="effective_from 需要 YYYY-MM-DD") from exc
    if version.is_current:
        current_rows = db.scalars(
            select(MetricVersion).where(MetricVersion.metric_id == metric.id, MetricVersion.is_current.is_(True))
        ).all()
        for row in current_rows:
            row.is_current = False
    db.add(version)
    db.flush()
    _sync_dsl_dependencies(db, metric, parsed["dependencies"])
    db.commit()
    db.refresh(version)
    log_event(
        "VERSION_CREATED",
        metric=metric.metric_key,
        version=version.version_no,
        team=team_id,
        agg=version.agg,
        grain=version.grain,
        window=version.window,
    )
    return version


def update_version(db: Session, user: User, version: MetricVersion, dsl_text: str) -> MetricVersion:
    metric = get_metric_or_404(db, version.metric_id)
    assert_can_edit_metric(user, metric)
    parsed = parse_or_raise(dsl_text)
    version.dsl_text = dsl_text.strip()
    _apply_parsed_tuple(version, parsed)
    _sync_dsl_dependencies(db, metric, parsed["dependencies"])
    db.commit()
    db.refresh(version)
    return version


def versions_for_metric(db: Session, metric_id: int) -> list[MetricVersion]:
    return list(
        db.scalars(
            select(MetricVersion)
            .where(MetricVersion.metric_id == metric_id)
            .order_by(MetricVersion.version_no)
        ).all()
    )


def compare_versions(db: Session, metric_id: int, version_a_id: int, version_b_id: int) -> dict:
    """Backend-computed five-tuple diff used by the version-comparison table."""
    from app.algorithms.conflict import diff_tuples, version_tuple

    metric = get_metric_or_404(db, metric_id)
    left = get_version_or_404(db, version_a_id)
    right = get_version_or_404(db, version_b_id)
    if left.metric_id != metric.id or right.metric_id != metric.id:
        raise AppError(ErrorCode.VERSION_NOT_FOUND, message="版本不属于该指标")
    left_tuple = version_tuple(left)
    right_tuple = version_tuple(right)
    diff = diff_tuples(left_tuple, right_tuple)
    teams = _team_map(db)
    return {
        "metric_id": metric.id,
        "metric_key": metric.metric_key,
        "version_a": serialize_version(left, teams.get(left.team_id)),
        "version_b": serialize_version(right, teams.get(right.team_id)),
        "tuple_a": left_tuple,
        "tuple_b": right_tuple,
        "dimensions": diff["dimensions"],
        "severity": diff["severity"],
        "conflict_type": diff["conflict_type"],
        "summary": diff["summary"],
        "evidence": diff["evidence"],
        "consistent": not diff["dimensions"],
        "checked_at": iso(None),
    }
