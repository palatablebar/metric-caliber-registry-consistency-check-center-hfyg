"""Consistency check batch lifecycle — mirrored by frontend/src/constants/checkStatus.ts."""
from enum import Enum


class CheckStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    # one or more in-scope selected versions could not be parsed / were missing /
    # changed after the batch started: partial figures only, never publishable as a normal completion
    INCOMPLETE = "incomplete"
    FAILED = "failed"


ALL_CHECK_STATUSES = [s.value for s in CheckStatus]
CHECK_STATUS_LABELS = {
    CheckStatus.PENDING.value: "排队中",
    CheckStatus.RUNNING.value: "检查中",
    CheckStatus.COMPLETED.value: "已完成",
    CheckStatus.INCOMPLETE.value: "不完整",
    CheckStatus.FAILED.value: "失败",
}
ACTIVE_STATUSES = (CheckStatus.PENDING.value, CheckStatus.RUNNING.value)
# terminal states whose findings/score must never be recomputed by a re-delivery
TERMINAL_STATUSES = (
    CheckStatus.COMPLETED.value,
    CheckStatus.INCOMPLETE.value,
    CheckStatus.FAILED.value,
)

# result trust policy: only a fully-complete run over an untouched input snapshot
# is authoritative enough to publish; everything else is explicitly untrusted.
TRUST_TRUSTED = "trusted"
TRUST_UNTRUSTED = "untrusted"
TRUST_PENDING = "pending"
TRUST_STATUS_LABELS = {
    TRUST_TRUSTED: "结果可信",
    TRUST_UNTRUSTED: "结果不可信",
    TRUST_PENDING: "结果未出",
}


def trust_status_for(check_status: str) -> str:
    if check_status == CheckStatus.COMPLETED.value:
        return TRUST_TRUSTED
    if check_status in (CheckStatus.INCOMPLETE.value, CheckStatus.FAILED.value):
        return TRUST_UNTRUSTED
    return TRUST_PENDING
