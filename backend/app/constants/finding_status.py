"""Conflict finding triage states."""
from enum import Enum


class FindingStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


ALL_FINDING_STATUSES = [s.value for s in FindingStatus]
FINDING_STATUS_LABELS = {
    FindingStatus.OPEN.value: "待处理",
    FindingStatus.ACKNOWLEDGED.value: "已确认",
    FindingStatus.RESOLVED.value: "已解决",
}
