"""Central error catalogue + AppError. Codes are mirrored in
frontend/src/constants/errorCodes.ts and rendered by ErrorNotice.vue."""
from enum import Enum


class ErrorCode(str, Enum):
    METRIC_NOT_FOUND = "MTR-1001"
    VERSION_NOT_FOUND = "MTR-1002"
    DSL_SYNTAX = "MTR-1003"
    DSL_SEMANTIC = "MTR-1004"
    METRIC_KEY_DUPLICATE = "MTR-1005"
    VERSION_CONFLICT = "MTR-1006"
    CHECK_NOT_FOUND = "MTR-1007"
    CHECK_RUNNING = "MTR-1008"
    FINDING_NOT_FOUND = "MTR-1009"
    QUOTA_EXHAUSTED = "MTR-1010"
    RATE_LIMITED = "MTR-1011"
    FORBIDDEN = "MTR-1012"
    UNAUTHORIZED = "MTR-1013"
    TEAM_NOT_FOUND = "MTR-1014"
    EXPORT_EMPTY = "MTR-1015"


ERROR_MESSAGES = {
    ErrorCode.METRIC_NOT_FOUND: "指标不存在或已删除",
    ErrorCode.VERSION_NOT_FOUND: "指标版本不存在",
    ErrorCode.DSL_SYNTAX: "DSL 语法错误",
    ErrorCode.DSL_SEMANTIC: "DSL 语义错误",
    ErrorCode.METRIC_KEY_DUPLICATE: "指标 key 已存在",
    ErrorCode.VERSION_CONFLICT: "版本号已被占用",
    ErrorCode.CHECK_NOT_FOUND: "一致性检查批次不存在",
    ErrorCode.CHECK_RUNNING: "已有检查批次在执行",
    ErrorCode.FINDING_NOT_FOUND: "冲突记录不存在",
    ErrorCode.QUOTA_EXHAUSTED: "今日检查配额已用尽",
    ErrorCode.RATE_LIMITED: "请求过于频繁",
    ErrorCode.FORBIDDEN: "当前角色或团队无权执行该操作",
    ErrorCode.UNAUTHORIZED: "未登录或登录已过期",
    ErrorCode.TEAM_NOT_FOUND: "团队不存在",
    ErrorCode.EXPORT_EMPTY: "该批次没有可导出的冲突记录",
}

ERROR_STATUS = {
    ErrorCode.METRIC_NOT_FOUND: 404,
    ErrorCode.VERSION_NOT_FOUND: 404,
    ErrorCode.DSL_SYNTAX: 422,
    ErrorCode.DSL_SEMANTIC: 422,
    ErrorCode.METRIC_KEY_DUPLICATE: 409,
    ErrorCode.VERSION_CONFLICT: 409,
    ErrorCode.CHECK_NOT_FOUND: 404,
    ErrorCode.CHECK_RUNNING: 409,
    ErrorCode.FINDING_NOT_FOUND: 404,
    ErrorCode.QUOTA_EXHAUSTED: 429,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.TEAM_NOT_FOUND: 404,
    ErrorCode.EXPORT_EMPTY: 409,
}


class AppError(Exception):
    def __init__(self, code, message: str | None = None, detail=None, context: str | None = None):
        self.code = code.value if isinstance(code, ErrorCode) else str(code)
        try:
            enum_code = ErrorCode(self.code)
        except ValueError:
            enum_code = None
        self.message = message or (ERROR_MESSAGES.get(enum_code, "请求处理失败") if enum_code else "请求处理失败")
        if context:
            self.message = f"{self.message}（{context}）"
        self.detail = detail
        self.status_code = ERROR_STATUS.get(enum_code, 400) if enum_code else 400
        super().__init__(self.message)
