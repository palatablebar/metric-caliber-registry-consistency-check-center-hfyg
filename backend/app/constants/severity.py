"""Conflict severity — mirrored by frontend/src/constants/severity.ts."""
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


ALL_SEVERITIES = [s.value for s in Severity]
SEVERITY_WEIGHT = {Severity.LOW.value: 1, Severity.MEDIUM.value: 2, Severity.HIGH.value: 3}
SEVERITY_LABELS = {Severity.LOW.value: "低", Severity.MEDIUM.value: "中", Severity.HIGH.value: "高"}
