"""Conflict dimension catalogue — mirrored by frontend/src/constants/conflictType.ts.

Severity mapping is fixed by governance policy:
  grain / filter / agg  -> high   (口径直接对不上)
  window                -> medium (时间范围不同，报表会差一截)
  measure               -> low    (度量字段不同，通常可解释)
"""
from enum import Enum

from app.constants.severity import Severity


class ConflictType(str, Enum):
    AGG = "agg"
    MEASURE = "measure"
    FILTER = "filter"
    WINDOW = "window"
    GRAIN = "grain"
    MULTI = "multi"


ALL_CONFLICT_TYPES = [c.value for c in ConflictType]
CONFLICT_LABELS = {
    ConflictType.AGG.value: "聚合函数",
    ConflictType.MEASURE.value: "度量字段",
    ConflictType.FILTER.value: "过滤集合",
    ConflictType.WINDOW.value: "时间窗口",
    ConflictType.GRAIN.value: "时间粒度",
    ConflictType.MULTI.value: "多维差异",
}
# dimension -> severity (policy from batch plan section 6)
DIMENSION_SEVERITY = {
    ConflictType.GRAIN.value: Severity.HIGH.value,
    ConflictType.FILTER.value: Severity.HIGH.value,
    ConflictType.AGG.value: Severity.HIGH.value,
    ConflictType.WINDOW.value: Severity.MEDIUM.value,
    ConflictType.MEASURE.value: Severity.LOW.value,
}
# penalty used by the consistency score (0-100)
DIMENSION_PENALTY = {Severity.HIGH.value: 3, Severity.MEDIUM.value: 2, Severity.LOW.value: 1}
DIMENSION_ORDER = [
    ConflictType.AGG.value,
    ConflictType.MEASURE.value,
    ConflictType.FILTER.value,
    ConflictType.WINDOW.value,
    ConflictType.GRAIN.value,
]
