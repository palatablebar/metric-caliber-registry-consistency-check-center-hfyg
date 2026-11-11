"""Metric lifecycle status — mirrored by frontend/src/constants/metricStatus.ts."""
from enum import Enum


class MetricStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


ALL_METRIC_STATUSES = [s.value for s in MetricStatus]
STATUS_LABELS = {
    MetricStatus.DRAFT.value: "草稿",
    MetricStatus.ACTIVE.value: "生效",
    MetricStatus.DEPRECATED.value: "已下线",
}
