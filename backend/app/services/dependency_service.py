"""Dependency graph projection + impact closure (downstream consumers)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.algorithms.graph import build_graph, impact_closure
from app.constants.error_codes import AppError, ErrorCode
from app.models import MetricDefinition, MetricDependency, OwnerTeam
from app.services.metric_service import get_metric_or_404


def _load(db: Session):
    metrics = db.scalars(select(MetricDefinition).order_by(MetricDefinition.metric_key)).all()
    edges = db.scalars(select(MetricDependency).order_by(MetricDependency.id)).all()
    metric_dicts = [
        {
            "id": metric.id,
            "key": metric.metric_key,
            "name": metric.display_name,
            "domain": metric.domain,
            "status": metric.status,
            "consumers": metric.consumers_json or [],
        }
        for metric in metrics
    ]
    edge_dicts = [
        {
            "from_id": edge.from_metric_id,
            "to_id": edge.to_metric_id,
            "to_table": edge.to_table,
            "relation": edge.relation,
            "note": edge.note,
        }
        for edge in edges
    ]
    return metrics, metric_dicts, edge_dicts


def graph_payload(db: Session) -> dict:
    metrics, metric_dicts, edge_dicts = _load(db)
    teams = {team.id: team for team in db.scalars(select(OwnerTeam)).all()}
    graph = build_graph(metric_dicts, [edge for edge in edge_dicts if edge["to_id"]])
    team_of = {metric.metric_key: teams.get(metric.owner_team_id) for metric in metrics}
    for node in graph["nodes"]:
        team = team_of.get(node["key"])
        node["team_code"] = team.code if team else None
        node["team_name"] = team.name if team else None
    table_edges = [edge for edge in edge_dicts if edge.get("to_table")]
    graph["table_edges"] = table_edges
    return graph


def impact_payload(db: Session, metric_id: int) -> dict:
    metric = get_metric_or_404(db, metric_id)
    _metrics, metric_dicts, edge_dicts = _load(db)
    closure = impact_closure(metric_id, metric_dicts, [edge for edge in edge_dicts if edge["to_id"]])
    closure["metric_name"] = metric.display_name
    closure["domain"] = metric.domain
    return closure
