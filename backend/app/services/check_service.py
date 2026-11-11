"""Consistency check batches: create → Celery execution → findings persisted.

``execute_check`` is the single real-computation path used both by the worker task
and by the demo seed, so the seeded batch is produced by the same algorithms the
API exposes (never hard-coded).
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.algorithms.conflict import build_findings, overall_score, version_tuple
from app.algorithms.dsl_parser import parse_dsl
from app.algorithms.graph import build_graph, impact_closure
from app.config.database import SessionLocal
from app.constants.check_status import CHECK_STATUS_LABELS, CheckStatus
from app.constants.conflict_type import CONFLICT_LABELS
from app.constants.domains import ALL_DOMAINS, DOMAIN_LABELS
from app.constants.error_codes import AppError, ErrorCode
from app.constants.finding_status import FINDING_STATUS_LABELS, FindingStatus
from app.constants.severity import SEVERITY_LABELS
from app.middlewares.quota import consume_check_quota, release_check_lock
from app.models import (
    ConflictFinding,
    ConsistencyCheck,
    MetricDefinition,
    MetricDependency,
    MetricVersion,
    User,
)
from app.utils.formatters import iso
from app.utils.logger import log_event


# --------------------------------------------------------------------------- helpers
def next_batch_no(db: Session, when: date | None = None) -> str:
    day = (when or date.today()).strftime("%Y%m%d")
    prefix = f"CHK-{day}-"
    count = int(
        db.scalar(
            select(func.count(ConsistencyCheck.id)).where(ConsistencyCheck.batch_no.like(prefix + "%"))
        )
        or 0
    )
    return f"{prefix}{count + 1:03d}"


def _scope_label(scope: str) -> str:
    return "全部域" if scope == "all" else DOMAIN_LABELS.get(scope, scope)


def _metric_dict(metric: MetricDefinition) -> dict:
    return {
        "id": metric.id,
        "key": metric.metric_key,
        "name": metric.display_name,
        "domain": metric.domain,
        "status": metric.status,
        "consumers": metric.consumers_json or [],
    }


def _load_graph_inputs(db: Session):
    metrics = db.scalars(select(MetricDefinition)).all()
    edges = db.scalars(select(MetricDependency)).all()
    metric_dicts = [_metric_dict(metric) for metric in metrics]
    edge_dicts = [
        {"from_id": edge.from_metric_id, "to_id": edge.to_metric_id, "relation": edge.relation}
        for edge in edges
    ]
    return metric_dicts, edge_dicts


# --------------------------------------------------------------------------- serialisation
def serialize_check(check: ConsistencyCheck) -> dict:
    duration_ms = None
    if check.started_at and check.finished_at:
        duration_ms = int((check.finished_at - check.started_at).total_seconds() * 1000)
    return {
        "id": check.id,
        "batch_no": check.batch_no,
        "scope": check.scope,
        "scope_label": _scope_label(check.scope),
        "status": check.status,
        "status_label": CHECK_STATUS_LABELS.get(check.status, check.status),
        "triggered_by": check.triggered_by,
        "started_at": iso(check.started_at),
        "finished_at": iso(check.finished_at),
        "metrics_checked": check.metrics_checked,
        "versions_checked": check.versions_checked,
        "conflict_count": check.conflict_count,
        "high_count": check.high_count,
        "consistency_score": check.consistency_score,
        "duration_ms": duration_ms,
        "summary": check.summary_json or {},
        "error_message": check.error_message,
        "created_at": iso(check.created_at),
    }


def serialize_finding(finding: ConflictFinding, metric_name: str | None = None) -> dict:
    return {
        "id": finding.id,
        "check_id": finding.check_id,
        "metric_id": finding.metric_id,
        "metric_key": finding.metric_key,
        "metric_name": metric_name,
        "conflict_type": finding.conflict_type,
        "conflict_label": CONFLICT_LABELS.get(finding.conflict_type, finding.conflict_type),
        "severity": finding.severity,
        "severity_label": SEVERITY_LABELS.get(finding.severity, finding.severity),
        "version_a_id": finding.version_a_id,
        "version_b_id": finding.version_b_id,
        "version_a_no": (finding.evidence_json or {}).get("version_a_no"),
        "version_b_no": (finding.evidence_json or {}).get("version_b_no"),
        "dimensions": finding.dimensions_json or [],
        "evidence": finding.evidence_json or {},
        "impact": finding.impact_json or {},
        "status": finding.status,
        "status_label": FINDING_STATUS_LABELS.get(finding.status, finding.status),
        "detail": finding.detail,
        "created_at": iso(finding.created_at),
    }


# --------------------------------------------------------------------------- create
def create_check(db: Session, user: User, scope: str) -> dict:
    scope = (scope or "all").strip()
    if scope != "all" and scope not in ALL_DOMAINS:
        raise AppError(ErrorCode.CHECK_NOT_FOUND, message="检查范围必须是 all 或一个业务域")
    active = db.scalar(
        select(ConsistencyCheck).where(
            ConsistencyCheck.status.in_([CheckStatus.PENDING.value, CheckStatus.RUNNING.value])
        )
    )
    if active is not None:
        raise AppError(
            ErrorCode.CHECK_RUNNING,
            message="已有检查批次正在执行，请稍后再试",
            detail={"batch_no": active.batch_no, "status": active.status},
        )
    consume_check_quota(db, user, scope)

    check = ConsistencyCheck(
        batch_no=next_batch_no(db),
        scope=scope,
        status=CheckStatus.PENDING.value,
        triggered_by=user.display_name or user.email,
        summary_json={},
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    log_event("CHECK_CREATED", batch=check.batch_no, scope=scope, actor=user.email)

    task_id = None
    try:
        from app.tasks.run_consistency_check import run_consistency_check_task

        async_result = run_consistency_check_task.delay(check.id)
        task_id = async_result.id
        log_event("CHECK_DISPATCHED", batch=check.batch_no, task_id=task_id)
    except Exception as exc:  # broker unavailable -> sync fallback so the demo still works
        log_event("CHECK_FAILED", batch=check.batch_no, reason=f"dispatch: {exc}")
        execute_check(check.id)

    db.refresh(check)
    payload = serialize_check(check)
    payload["task_id"] = task_id
    return payload


# --------------------------------------------------------------------------- execute
def execute_check(check_id: int) -> dict:
    db = SessionLocal()
    check = db.get(ConsistencyCheck, check_id)
    if check is None:
        db.close()
        return {}
    if check.status == CheckStatus.COMPLETED.value:
        summary = check.summary_json or {}
        db.close()
        return summary
    try:
        check.status = CheckStatus.RUNNING.value
        check.started_at = datetime.now()
        db.commit()
        log_event("CHECK_STARTED", batch=check.batch_no, check_id=check.id)

        metric_query = select(MetricDefinition).order_by(MetricDefinition.metric_key)
        if check.scope != "all":
            metric_query = metric_query.where(MetricDefinition.domain == check.scope)
        metrics = list(db.scalars(metric_query).all())
        metric_by_key = {metric.metric_key: metric for metric in metrics}

        groups: list[list[dict]] = []
        parse_failed: list[dict] = []
        versions_checked = 0
        for metric in metrics:
            versions = list(
                db.scalars(
                    select(MetricVersion)
                    .where(MetricVersion.metric_id == metric.id)
                    .order_by(MetricVersion.version_no)
                ).all()
            )
            versions_checked += len(versions)
            parsed_versions: list[dict] = []
            for version in versions:
                parsed = parse_dsl(version.dsl_text)
                if parsed["ok"]:
                    version.agg = parsed["agg"]
                    version.measure = parsed["measure"]
                    version.source_table = parsed["source_table"]
                    version.filters_json = parsed["filters"]
                    version.window = parsed["window"]
                    version.grain = parsed["grain"]
                    version.parse_status = "ok"
                    version.parse_error = None
                    parsed_versions.append(
                        {
                            "id": version.id,
                            "version_no": version.version_no,
                            "metric_key": metric.metric_key,
                            "team_id": version.team_id,
                            **version_tuple(parsed["tuple"]),
                        }
                    )
                else:
                    version.parse_status = "error"
                    version.parse_error = parsed["error"]
                    parse_failed.append(
                        {
                            "metric_key": metric.metric_key,
                            "version_no": version.version_no,
                            "error": parsed["error"],
                            "offset": parsed["error_offset"],
                        }
                    )
            # only >=2 successfully parsed versions can conflict
            if len(parsed_versions) >= 2:
                groups.append(parsed_versions)

        findings_data: list[dict] = []
        for versions in groups:
            metric = metric_by_key[versions[0]["metric_key"]]
            findings_data.extend(build_findings(_metric_dict(metric), versions))

        graph_metrics, graph_edges = _load_graph_inputs(db)
        graph = build_graph(graph_metrics, [edge for edge in graph_edges if edge["to_id"]])

        impact_cache: dict[int, dict] = {}
        for finding in findings_data:
            metric_id = finding["metric_id"]
            if metric_id not in impact_cache:
                impact_cache[metric_id] = impact_closure(
                    metric_id, graph_metrics, [edge for edge in graph_edges if edge["to_id"]]
                )
            finding["impact"] = impact_cache[metric_id]
            finding["status"] = FindingStatus.OPEN.value

        db.execute(delete(ConflictFinding).where(ConflictFinding.check_id == check.id))
        for finding in findings_data:
            db.add(
                ConflictFinding(
                    check_id=check.id,
                    metric_id=finding["metric_id"],
                    metric_key=finding["metric_key"],
                    conflict_type=finding["conflict_type"],
                    severity=finding["severity"],
                    version_a_id=finding["version_a_id"],
                    version_b_id=finding["version_b_id"],
                    dimensions_json=finding["dimensions"],
                    evidence_json=finding["evidence"],
                    impact_json=finding["impact"],
                    detail=finding["detail"],
                    status=finding["status"],
                )
            )

        scored = overall_score(groups)
        high_count = sum(1 for finding in findings_data if finding["severity"] == "high")
        check.metrics_checked = len(metrics)
        check.versions_checked = versions_checked
        check.conflict_count = len(findings_data)
        check.high_count = high_count
        check.consistency_score = int(scored["score"])
        check.summary_json = {
            "score": scored["score"],
            "pairs_compared": scored["pairs_compared"],
            "metric_scores": scored["metric_scores"],
            "metrics_with_multiple_versions": len(groups),
            "cycles": [
                {"member_keys": cycle["member_keys"], "path_keys": cycle["path_keys"]} for cycle in graph["cycles"]
            ],
            "orphans": graph["orphans"],
            "topological_order": graph["topological_order"],
            "graph_stats": graph["stats"],
            "parse_failed": parse_failed,
            "findings_by_dimension": _count_dimensions(findings_data),
        }
        check.status = CheckStatus.COMPLETED.value
        check.finished_at = datetime.now()
        check.error_message = None
        db.commit()
        log_event(
            "CHECK_FINISHED",
            batch=check.batch_no,
            versions=versions_checked,
            findings=len(findings_data),
            high=high_count,
            score=check.consistency_score,
        )
        summary = serialize_check(check)
        release_check_lock(check.scope)
        db.close()
        return summary
    except Exception as exc:
        db.rollback()
        failed = db.get(ConsistencyCheck, check_id)
        if failed is not None:
            failed.status = CheckStatus.FAILED.value
            failed.finished_at = datetime.now()
            failed.error_message = f"{type(exc).__name__}: {exc}"
            db.commit()
        log_event("CHECK_FAILED", batch=check_id, reason=str(exc))
        db.close()
        raise
    finally:
        try:
            db.close()
        except Exception:
            pass


def _count_dimensions(findings: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        for dimension in finding["dimensions"]:
            counts[dimension] = counts.get(dimension, 0) + 1
    return counts


# --------------------------------------------------------------------------- queries
def list_checks(db: Session, page: int = 1, page_size: int = 10) -> dict:
    from app.utils.pagination import paginate

    stmt = select(ConsistencyCheck).order_by(ConsistencyCheck.created_at.desc(), ConsistencyCheck.id.desc())
    items, total = paginate(db, stmt, page, page_size)
    return {
        "items": [serialize_check(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_check_or_404(db: Session, check_id: int) -> ConsistencyCheck:
    check = db.get(ConsistencyCheck, check_id)
    if check is None:
        raise AppError(ErrorCode.CHECK_NOT_FOUND, detail={"check_id": check_id})
    return check


def get_latest_check(db: Session) -> ConsistencyCheck | None:
    return db.scalar(select(ConsistencyCheck).order_by(ConsistencyCheck.id.desc()))


def check_detail(db: Session, check_id: int, include_findings: bool = True) -> dict:
    check = get_check_or_404(db, check_id)
    data = serialize_check(check)
    if include_findings:
        finding_rows = list(
            db.scalars(
                select(ConflictFinding)
                .where(ConflictFinding.check_id == check.id)
                .order_by(ConflictFinding.severity.desc(), ConflictFinding.id)
            ).all()
        )
        metric_ids = {finding.metric_id for finding in finding_rows}
        names = {
            metric.id: metric.display_name
            for metric in db.scalars(select(MetricDefinition).where(MetricDefinition.id.in_(metric_ids))).all()
        } if metric_ids else {}
        data["findings"] = [
            serialize_finding(finding, names.get(finding.metric_id)) for finding in finding_rows
        ]
    return data


def triage_finding(db: Session, finding: ConflictFinding, status: str) -> ConflictFinding:
    if status not in [value.value for value in FindingStatus]:
        raise AppError(ErrorCode.FINDING_NOT_FOUND, message="冲突状态只能是 open/acknowledged/resolved")
    finding.status = status
    db.commit()
    db.refresh(finding)
    return finding


def impact_csv(db: Session, check_id: int) -> tuple[str, str]:
    from app.utils.csv_export import render_impact_csv

    check = get_check_or_404(db, check_id)
    findings = list(
        db.scalars(
            select(ConflictFinding)
            .where(ConflictFinding.check_id == check.id)
            .order_by(ConflictFinding.severity.desc(), ConflictFinding.id)
        ).all()
    )
    if not findings:
        raise AppError(ErrorCode.EXPORT_EMPTY, detail={"batch_no": check.batch_no})
    metric_names = {
        metric.id: metric.display_name
        for metric in db.scalars(
            select(MetricDefinition).where(
                MetricDefinition.id.in_({finding.metric_id for finding in findings})
            )
        ).all()
    }
    rows = [
        {
            "metric_key": finding.metric_key,
            "metric_name": metric_names.get(finding.metric_id),
            "conflict_type": finding.conflict_type,
            "severity": finding.severity,
            "version_a_no": (finding.evidence_json or {}).get("version_a_no")
            or _version_no(db, finding.version_a_id),
            "version_b_no": (finding.evidence_json or {}).get("version_b_no")
            or _version_no(db, finding.version_b_id),
            "dimensions": finding.dimensions_json,
            "impact": finding.impact_json,
            "detail": finding.detail,
        }
        for finding in findings
    ]
    return f"impact-{check.batch_no}.csv", render_impact_csv(check.batch_no, rows)


def _version_no(db: Session, version_id: int) -> int | None:
    version = db.get(MetricVersion, version_id)
    return version.version_no if version else None
