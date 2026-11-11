"""Roles — backend source of truth, mirrored by frontend/src/constants/roles.ts."""
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    OWNER = "owner"
    ANALYST = "analyst"


ALL_ROLES = [r.value for r in Role]
WRITE_ROLES = (Role.ADMIN.value, Role.OWNER.value)
ROLE_LABELS = {
    Role.ADMIN.value: "治理委员会管理员",
    Role.OWNER.value: "指标负责人",
    Role.ANALYST.value: "分析员（只读）",
}
