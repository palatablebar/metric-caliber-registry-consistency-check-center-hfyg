"""Frozen input snapshots for consistency check batches.

A snapshot is taken synchronously when the batch is created — *before* the Celery
worker starts — and captures exactly which metrics, versions (with the DSL text
hash the worker must verify) and dependency edges belong to this round. The worker
only reads what the snapshot lists, so a version submitted (or edited) while the
batch is in flight can never be mixed into this run.

The whole snapshot is canonicalised and SHA-256 fingerprinted; each version also
carries its own DSL hash. Both are shown on the check page and logged, giving the
governance committee a verifiable record of what was actually checked.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.domains import ALL_DOMAINS
from app.models import MetricDefinition, MetricDependency, MetricVersion
from app.utils.formatters import iso

SNAPSHOT_VERSION = 1


def canonical_json(payload: dict | list) -> str:
    """Stable JSON text (sorted keys, no whitespace) used for hashing."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def dsl_hash(dsl_text: str | None) -> str:
    return hashlib.sha256((dsl_text or "").encode("utf-8")).hexdigest()


def _fingerprint(payload: dict) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def build_input_snapshot(db: Session, scope: str) -> dict:
    """Freeze the complete check input for ``scope`` at batch-creation time."""
    scope = (scope or "all").strip()
    if scope != "all" and scope not in ALL_DOMAINS:
        from app.constants.error_codes import AppError, ErrorCode

        raise AppError(ErrorCode.CHECK_NOT_FOUND, message="检查范围必须是 all 或一个业务域")

    metric_query = select(MetricDefinition).order_by(MetricDefinition.metric_key, MetricDefinition.id)
    if scope != "all":
        metric_query = metric_query.where(MetricDefinition.domain == scope)
    metrics = list(db.scalars(metric_query).all())
    metric_ids = [metric.id for metric in metrics]

    version_rows = list(
        db.scalars(
            select(MetricVersion)
            .where(MetricVersion.metric_id.in_(metric_ids or [-1]))
            .order_by(MetricVersion.metric_id, MetricVersion.version_no, MetricVersion.id)
        ).all()
    )
    versions_by_metric: dict[int, list[MetricVersion]] = {}
    for row in version_rows:
        versions_by_metric.setdefault(row.metric_id, []).append(row)

    edge_rows = list(
        db.scalars(
            select(MetricDependency).where(
                MetricDependency.from_metric_id.in_(metric_ids or [-1]),
                MetricDependency.to_metric_id.is_not(None),
            )
        ).all()
    )

    snapshot_metrics: list[dict] = []
    snapshot_versions: list[dict] = []
    for metric in metrics:
        snapshot_metrics.append(
            {
                "id": metric.id,
                "key": metric.metric_key,
                "name": metric.display_name,
                "domain": metric.domain,
                "status": metric.status,
                "team_id": metric.owner_team_id,
                "consumers": metric.consumers_json or [],
                "version_ids": [row.id for row in versions_by_metric.get(metric.id, [])],
            }
        )
        for row in versions_by_metric.get(metric.id, []):
            snapshot_versions.append(
                {
                    "id": row.id,
                    "metric_id": row.metric_id,
                    "metric_key": metric.metric_key,
                    "version_no": row.version_no,
                    "team_id": row.team_id,
                    "dsl_sha256": dsl_hash(row.dsl_text),
                    "dsl_chars": len(row.dsl_text or ""),
                    "created_at": iso(row.created_at),
                }
            )

    snapshot_edges = [
        {
            "from_metric_id": edge.from_metric_id,
            "to_metric_id": edge.to_metric_id,
            "relation": edge.relation,
        }
        for edge in edge_rows
    ]

    captured_at = datetime.now()
    snapshot = {
        "snapshot_version": SNAPSHOT_VERSION,
        "scope": scope,
        "captured_at": iso(captured_at),
        "metric_count": len(snapshot_metrics),
        "version_count": len(snapshot_versions),
        "edge_count": len(snapshot_edges),
        "metrics": snapshot_metrics,
        "versions": snapshot_versions,
        "edges": snapshot_edges,
    }
    # The fingerprint covers content only (not captured_at), so the committee can
    # recompute it from the frozen metric/version/edge list and prove two rounds
    # really used the same input.
    snapshot["fingerprint"] = _fingerprint(
        {
            "snapshot_version": snapshot["snapshot_version"],
            "scope": snapshot["scope"],
            "metrics": snapshot_metrics,
            "versions": snapshot_versions,
            "edges": snapshot_edges,
        }
    )
    return snapshot
