"""Consistency check batch lifecycle — mirrored by frontend/src/constants/checkStatus.ts."""
from enum import Enum


class CheckStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


ALL_CHECK_STATUSES = [s.value for s in CheckStatus]
CHECK_STATUS_LABELS = {
    CheckStatus.PENDING.value: "排队中",
    CheckStatus.RUNNING.value: "检查中",
    CheckStatus.COMPLETED.value: "已完成",
    CheckStatus.FAILED.value: "失败",
}
ACTIVE_STATUSES = (CheckStatus.PENDING.value, CheckStatus.RUNNING.value)
