"""Role checks as FastAPI dependencies. Resource-level ownership checks
(an owner may only edit metrics of their own team) live in metric/version services."""
from fastapi import Depends

from app.constants.error_codes import AppError, ErrorCode
from app.constants.roles import Role
from app.middlewares.auth import get_current_user
from app.models import User


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppError(
                ErrorCode.FORBIDDEN,
                message=f"当前角色 {user.role} 无权执行该操作，需要 {'/'.join(roles)}",
                detail={"required_roles": list(roles), "role": user.role},
            )
        return user

    return dependency


def require_admin(user: User = Depends(get_current_user)) -> User:
    return require_roles(Role.ADMIN.value)(user)


def assert_can_edit_metric(user: User, metric) -> None:
    """admin: any metric; owner: only their team's metric; analyst: never."""
    if user.role == Role.ADMIN.value:
        return
    if user.role == Role.OWNER.value:
        if metric.owner_team_id == user.team_id:
            return
        raise AppError(
            ErrorCode.FORBIDDEN,
            message="只能修改本团队负责的指标口径",
            detail={
                "role": user.role,
                "user_team_id": user.team_id,
                "metric_team_id": metric.owner_team_id,
                "metric_key": metric.metric_key,
            },
        )
    raise AppError(
        ErrorCode.FORBIDDEN,
        message="只读分析员不能修改指标",
        detail={"role": user.role},
    )
