"""Metric definitions: catalog listing, detail with versions/dependencies, CRUD."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.constants.domains import DOMAIN_LABELS, DOMAIN_ORDER
from app.constants.error_codes import AppError, ErrorCode
from app.constants.metric_status import STATUS_LABELS
from app.middlewares.rbac import assert_can_edit_metric
from app.models import MetricDefinition, MetricDependency, MetricVersion, OwnerTeam, User
from app.utils.formatters import iso
from app.utils.logger import log_event
from app.utils.pagination import paginate


def serialize_version(version: MetricVersion | None, team: OwnerTeam | None = None) -> dict | None:
    if version is None:
        return None
    return {
        "id": version.id,
        "metric_id": version.metric_id,
        "version_no": version.version_no,
        "team_id": version.team_id,
        "team_code": team.code if team else None,
        "team_name": team.name if team else None,
        "dsl_text": version.dsl_text,
        "agg": version.agg,
        "measure": version.measure,
        "source_table": version.source_table,
        "filters": version.filters_json or [],
        "window": version.window,
        "grain": version.grain,
        "parse_status": version.parse_status,
        "parse_error": version.parse_error,
        "is_current": bool(version.is_current),
        "effective_from": iso(version.effective_from),
        "created_by": version.created_by,
        "created_at": iso(version.created_at),
        "tuple": {
            "agg": version.agg,
            "measure": version.measure,
            "filters": version.filters_json or [],
            "window": version.window,
            "grain": version.grain,
        },
    }


def load_versions_for(db: Session, metric_ids: list[int]) -> dict[int, list[MetricVersion]]:
    if not metric_ids:
        return {}
    versions = db.scalars(
        select(MetricVersion)
        .where(MetricVersion.metric_id.in_(metric_ids))
        .order_by(MetricVersion.metric_id, MetricVersion.version_no)
    ).all()
    grouped: dict[int, list[MetricVersion]] = {metric_id: [] for metric_id in metric_ids}
    for version in versions:
        grouped.setdefault(version.metric_id, []).append(version)
    return grouped


def _team_map(db: Session) -> dict[int, OwnerTeam]:
    return {team.id: team for team in db.scalars(select(OwnerTeam)).all()}


def serialize_metric(metric: MetricDefinition, versions: list[MetricVersion], teams: dict[int, OwnerTeam]) -> dict:
    ordered = sorted(versions, key=lambda version: version.version_no)
    current = next((version for version in reversed(ordered) if version.is_current), ordered[-1] if ordered else None)
    return {
        "id": metric.id,
        "key": metric.metric_key,
        "name": metric.display_name,
        "domain": metric.domain,
        "domain_label": DOMAIN_LABELS.get(metric.domain, metric.domain),
        "status": metric.status,
        "status_label": STATUS_LABELS.get(metric.status, metric.status),
        "owner_team": {
            "id": metric.owner_team_id,
            "code": teams.get(metric.owner_team_id).code if teams.get(metric.owner_team_id) else None,
            "name": teams.get(metric.owner_team_id).name if teams.get(metric.owner_team_id) else None,
        },
        "description": metric.description,
        "consumers": metric.consumers_json or [],
        "version_count": len(ordered),
        "team_count": len({version.team_id for version in ordered}),
        "current_version": serialize_version(current, teams.get(current.team_id) if current else None),
        "updated_at": iso(metric.updated_at),
    }


def _domain_counts(db: Session) -> dict[str, int]:
    from sqlalchemy import func

    counts = {domain: 0 for domain in DOMAIN_ORDER}
    rows = db.execute(
        select(MetricDefinition.domain, func.count(MetricDefinition.id)).group_by(MetricDefinition.domain)
    ).all()
    for domain, total in rows:
        counts[str(domain)] = int(total)
    return counts


def list_metrics(
    db: Session,
    q: str | None = None,
    domain: str | None = None,
    status: str | None = None,
    team_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    stmt = select(MetricDefinition)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                MetricDefinition.metric_key.like(pattern),
                MetricDefinition.display_name.like(pattern),
                MetricDefinition.description.like(pattern),
            )
        )
    if domain:
        stmt = stmt.where(MetricDefinition.domain == domain)
    if status:
        stmt = stmt.where(MetricDefinition.status == status)
    if team_id:
        stmt = stmt.where(MetricDefinition.owner_team_id == team_id)
    stmt = stmt.order_by(MetricDefinition.domain, MetricDefinition.metric_key)
    items, total = paginate(db, stmt, page, page_size)
    versions_map = load_versions_for(db, [item.id for item in items])
    teams = _team_map(db)
    return {
        "items": [serialize_metric(item, versions_map.get(item.id, []), teams) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "domain_counts": _domain_counts(db),
        "domains": [{"value": domain, "label": DOMAIN_LABELS[domain]} for domain in DOMAIN_ORDER],
    }


def get_metric_or_404(db: Session, metric_id: int) -> MetricDefinition:
    metric = db.get(MetricDefinition, metric_id)
    if metric is None:
        raise AppError(ErrorCode.METRIC_NOT_FOUND, detail={"metric_id": metric_id})
    return metric


def get_metric_detail(db: Session, metric_id: int) -> dict:
    metric = get_metric_or_404(db, metric_id)
    versions = db.scalars(
        select(MetricVersion).where(MetricVersion.metric_id == metric.id).order_by(MetricVersion.version_no)
    ).all()
    teams = _team_map(db)
    data = serialize_metric(metric, list(versions), teams)
    data["versions"] = [serialize_version(version, teams.get(version.team_id)) for version in versions]

    outgoing = db.scalars(select(MetricDependency).where(MetricDependency.from_metric_id == metric.id)).all()
    incoming = db.scalars(select(MetricDependency).where(MetricDependency.to_metric_id == metric.id)).all()
    upstream_metrics: list[dict] = []
    tables: list[dict] = []
    for edge in outgoing:
        if edge.to_metric_id:
            target = db.get(MetricDefinition, edge.to_metric_id)
            if target:
                upstream_metrics.append(
                    {
                        "edge_id": edge.id,
                        "id": target.id,
                        "key": target.metric_key,
                        "name": target.display_name,
                        "domain": target.domain,
                        "relation": edge.relation,
                        "note": edge.note,
                    }
                )
        elif edge.to_table:
            tables.append({"edge_id": edge.id, "table": edge.to_table, "relation": edge.relation, "note": edge.note})
    downstream_metrics: list[dict] = []
    for edge in incoming:
        if edge.from_metric_id:
            consumer = db.get(MetricDefinition, edge.from_metric_id)
            if consumer:
                downstream_metrics.append(
                    {
                        "edge_id": edge.id,
                        "id": consumer.id,
                        "key": consumer.metric_key,
                        "name": consumer.display_name,
                        "domain": consumer.domain,
                        "relation": edge.relation,
                    }
                )
    data["dependencies"] = {
        "upstream": upstream_metrics,
        "downstream": downstream_metrics,
        "tables": tables,
    }
    return data


def create_metric(db: Session, user: User, payload) -> MetricDefinition:
    existing = db.scalar(select(MetricDefinition).where(MetricDefinition.metric_key == payload.metric_key))
    if existing:
        raise AppError(
            ErrorCode.METRIC_KEY_DUPLICATE,
            detail={"metric_key": payload.metric_key, "metric_id": existing.id},
        )
    team = db.get(OwnerTeam, payload.owner_team_id)
    if team is None:
        raise AppError(ErrorCode.TEAM_NOT_FOUND, detail={"team_id": payload.owner_team_id})
    if user.role == "owner" and payload.owner_team_id != user.team_id:
        raise AppError(
            ErrorCode.FORBIDDEN,
            message="只能为本团队注册指标",
            detail={"user_team_id": user.team_id, "requested_team_id": payload.owner_team_id},
        )
    metric = MetricDefinition(
        metric_key=payload.metric_key,
        display_name=payload.display_name,
        domain=payload.domain or team.domain,
        owner_team_id=payload.owner_team_id,
        status=payload.status,
        description=payload.description,
        consumers_json=payload.consumers or [],
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    log_event("METRIC_CREATED", metric=metric.metric_key, team=team.code, actor=user.email)
    return metric


def update_metric(db: Session, user: User, metric: MetricDefinition, payload) -> MetricDefinition:
    assert_can_edit_metric(user, metric)
    before = {
        "display_name": metric.display_name,
        "status": metric.status,
        "description": metric.description,
        "consumers": metric.consumers_json,
        "owner_team_id": metric.owner_team_id,
    }
    if payload.owner_team_id is not None and payload.owner_team_id != metric.owner_team_id:
        if user.role != "admin":
            raise AppError(ErrorCode.FORBIDDEN, message="只有管理员可以转移指标归属团队")
        if db.get(OwnerTeam, payload.owner_team_id) is None:
            raise AppError(ErrorCode.TEAM_NOT_FOUND, detail={"team_id": payload.owner_team_id})
        metric.owner_team_id = payload.owner_team_id
    if payload.display_name is not None:
        metric.display_name = payload.display_name
    if payload.status is not None:
        metric.status = payload.status
    if payload.description is not None:
        metric.description = payload.description
    if payload.consumers is not None:
        metric.consumers_json = payload.consumers
    db.commit()
    db.refresh(metric)
    log_event("METRIC_UPDATED", metric=metric.metric_key, fields=",".join(before.keys()), actor=user.email)
    return metric
