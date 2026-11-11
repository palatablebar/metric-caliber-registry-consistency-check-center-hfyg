"""Metric caliber conflict detection + consistency scoring + impact closure.

The governor policy compares the same-named metric versions through the five-tuple
``(agg, measure, filter set, window, grain)``:

    grain / filter / agg -> high
    window               -> medium
    measure              -> low

Consistency score (0-100) = 100 * (1 - sum(pair penalties) / (pairs * 12)), where
each differing dimension contributes its severity weight (high=3, medium=2, low=1)
and a pair can differ in at most 3*3 + 2 + 1 = 12 penalty points.
"""
from __future__ import annotations

from typing import Any

from app.algorithms.graph import build_graph
from app.constants.conflict_type import (
    DIMENSION_ORDER,
    DIMENSION_PENALTY,
    DIMENSION_SEVERITY,
)
from app.constants.severity import SEVERITY_WEIGHT

TUPLE_FIELDS = ("agg", "measure", "filters", "window", "grain")

# tuple field -> public conflict dimension (the filter dimension is singular)
FIELD_TO_DIMENSION = {
    "agg": "agg",
    "measure": "measure",
    "filters": "filter",
    "window": "window",
    "grain": "grain",
}


def version_tuple(version: dict[str, Any] | Any) -> dict[str, Any]:
    get = version.get if isinstance(version, dict) else lambda key, default=None: getattr(version, key, default)
    filters = get("filters_json", None)
    if filters is None:
        filters = get("filters", [])
    filters = filters or []
    return {
        "agg": (get("agg") or "").strip().lower(),
        "measure": (get("measure") or "").strip().lower(),
        "filters": sorted(str(item) for item in filters),
        "window": (get("window") or "all").strip().lower(),
        "grain": (get("grain") or "").strip().lower(),
    }


def diff_tuples(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Pairwise five-tuple diff. Returns dimensions, severity and evidence rows."""
    differing: list[str] = []
    evidence: dict[str, dict[str, Any]] = {}
    for field in TUPLE_FIELDS:
        if left.get(field) != right.get(field):
            dimension = FIELD_TO_DIMENSION[field]
            differing.append(dimension)
            evidence[dimension] = {
                "field": field,
                "left": left.get(field),
                "right": right.get(field),
            }
    if not differing:
        return {
            "dimensions": [],
            "severity": None,
            "conflict_type": None,
            "max_penalty": 0,
            "evidence": {},
            "summary": "五元组完全一致",
        }
    severities = [DIMENSION_SEVERITY[field] for field in differing]
    top = max(severities, key=lambda value: SEVERITY_WEIGHT[value])
    max_penalty = sum(DIMENSION_PENALTY[severity] for severity in severities)
    ordered = [field for field in DIMENSION_ORDER if field in differing]
    return {
        "dimensions": ordered,
        "severity": top,
        "conflict_type": ordered[0] if len(ordered) == 1 else "multi",
        "max_penalty": max_penalty,
        "evidence": evidence,
        "summary": _diff_summary(left, right, ordered),
    }


DIMENSION_TO_FIELD = {dimension: field for field, dimension in FIELD_TO_DIMENSION.items()}


def _diff_summary(left: dict[str, Any], right: dict[str, Any], dimensions: list[str]) -> str:
    labels = {
        "agg": "聚合函数",
        "measure": "度量字段",
        "filter": "过滤集合",
        "window": "时间窗口",
        "grain": "时间粒度",
    }
    parts = []
    for dimension in dimensions:
        field = DIMENSION_TO_FIELD[dimension]
        parts.append(f"{labels[dimension]} {left.get(field)} → {right.get(field)}")
    return "；".join(parts)


def score_metric_group(versions: list[dict[str, Any]]) -> dict[str, Any]:
    """Score one same-named metric group (all C(n,2) pairs)."""
    pairs: list[dict[str, Any]] = []
    total_penalty = 0
    for i in range(len(versions)):
        for j in range(i + 1, len(versions)):
            left, right = versions[i], versions[j]
            diff = diff_tuples(version_tuple(left), version_tuple(right))
            total_penalty += diff["max_penalty"]
            pairs.append(
                {
                    "version_a": left.get("id"),
                    "version_b": right.get("id"),
                    "version_a_no": left.get("version_no"),
                    "version_b_no": right.get("version_no"),
                    "dimensions": diff["dimensions"],
                    "severity": diff["severity"],
                    "conflict_type": diff["conflict_type"],
                    "summary": diff["summary"],
                }
            )
    max_possible = len(pairs) * 12
    score = 100 if max_possible == 0 else max(0, round(100 * (1 - total_penalty / max_possible)))
    return {"pairs": pairs, "score": score, "penalty": total_penalty, "pairs_compared": len(pairs)}


def build_findings(metric: dict[str, Any], versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """All pairwise findings for one metric group, ordered by severity then version."""
    findings: list[dict[str, Any]] = []
    for i in range(len(versions)):
        for j in range(i + 1, len(versions)):
            left, right = versions[i], versions[j]
            diff = diff_tuples(version_tuple(left), version_tuple(right))
            if not diff["dimensions"]:
                continue
            findings.append(
                {
                    "metric_id": metric["id"],
                    "metric_key": metric["key"],
                    "version_a_id": left.get("id"),
                    "version_b_id": right.get("id"),
                    "version_a_no": left.get("version_no"),
                    "version_b_no": right.get("version_no"),
                    "conflict_type": diff["conflict_type"],
                    "severity": diff["severity"],
                    "dimensions": diff["dimensions"],
                    "evidence": {
                        "left": version_tuple(left),
                        "right": version_tuple(right),
                        "diff": diff["evidence"],
                        "version_a_no": left.get("version_no"),
                        "version_b_no": right.get("version_no"),
                    },
                    "detail": f"{metric['key']} v{left.get('version_no')} vs v{right.get('version_no')}：{diff['summary']}",
                }
            )
    order = {field: index for index, field in enumerate(DIMENSION_ORDER)}
    findings.sort(
        key=lambda item: (
            -SEVERITY_WEIGHT[item["severity"]],
            order.get(item["dimensions"][0], 99),
            item["version_a_no"],
            item["version_b_no"],
        )
    )
    return findings


def overall_score(groups: list[list[dict[str, Any]]]) -> dict[str, Any]:
    total_penalty = 0
    total_pairs = 0
    metric_scores: dict[str, int] = {}
    for versions in groups:
        if len(versions) < 2:
            continue
        scored = score_metric_group(versions)
        total_penalty += scored["penalty"]
        total_pairs += scored["pairs_compared"]
        metric_scores[str(versions[0].get("metric_key"))] = scored["score"]
    max_possible = total_pairs * 12
    score = 100 if max_possible == 0 else max(0, round(100 * (1 - total_penalty / max_possible)))
    return {
        "score": score,
        "total_penalty": total_penalty,
        "pairs_compared": total_pairs,
        "metric_scores": metric_scores,
    }


__all__ = [
    "TUPLE_FIELDS",
    "version_tuple",
    "diff_tuples",
    "score_metric_group",
    "build_findings",
    "overall_score",
    "build_graph",
]
