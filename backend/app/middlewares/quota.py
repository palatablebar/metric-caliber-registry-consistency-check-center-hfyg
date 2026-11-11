"""Check quota + Redis sliding-window rate limit + per-scope check lock.

* daily quota: users.daily_check_quota / quota_used / quota_used_date
* sliding window: zset ``rl:metricd:{user_id}``
* check lock: SETNX ``checklock:{scope}`` so two batches never run at once
"""
import time
from datetime import date

import redis
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings
from app.constants.error_codes import AppError, ErrorCode
from app.models import User
from app.utils.logger import log_event

_client = None
_mem_window: dict[str, list[float]] = {}
_mem_locks: dict[str, float] = {}

RATE_LIMIT_BYPASS = ("/auth/login", "/dsl/parse")
RATE_LIMIT_WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


def get_redis():
    global _client
    if _client is None:
        try:
            _client = redis.Redis.from_url(
                settings.REDIS_URL, socket_timeout=0.4, socket_connect_timeout=0.4, decode_responses=True
            )
            _client.ping()
        except Exception:
            _client = False
    return _client or None


def rate_limit_allow(user_id: int) -> bool:
    window = settings.RATE_WINDOW_SECONDS
    max_hits = settings.RATE_WINDOW_MAX
    now = time.time()
    key = f"rl:metricd:{user_id}"
    client = get_redis()
    if client is not None:
        try:
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zadd(key, {f"{now:.6f}": now})
            pipe.zcard(key)
            pipe.expire(key, window)
            _, _, count, _ = pipe.execute()
            allowed = int(count) <= max_hits
        except Exception:
            allowed = _mem_allow(key, now, window, max_hits)
    else:
        allowed = _mem_allow(key, now, window, max_hits)
    if not allowed:
        log_event("AUDIT_RATE_LIMITED", user_id=user_id, window_max=max_hits)
    return allowed


def _mem_allow(key: str, now: float, window: int, max_hits: int) -> bool:
    hits = [stamp for stamp in _mem_window.get(key, []) if stamp > now - window]
    hits.append(now)
    _mem_window[key] = hits
    return len(hits) <= max_hits


def acquire_check_lock(scope: str) -> bool:
    key = f"checklock:{scope}"
    client = get_redis()
    if client is not None:
        try:
            return bool(client.set(key, "1", nx=True, ex=settings.CHECK_LOCK_TTL_SECONDS))
        except Exception:
            pass
    expiry = _mem_locks.get(key)
    if expiry and expiry > time.time():
        return False
    _mem_locks[key] = time.time() + settings.CHECK_LOCK_TTL_SECONDS
    return True


def release_check_lock(scope: str) -> None:
    key = f"checklock:{scope}"
    client = get_redis()
    if client is not None:
        try:
            client.delete(key)
        except Exception:
            pass
    _mem_locks.pop(key, None)


def quota_snapshot(user: User) -> dict:
    quota = int(user.daily_check_quota or 0)
    used = int(user.quota_used or 0)
    return {
        "daily_check_quota": quota,
        "quota_used": used,
        "quota_remaining": max(0, quota - used),
        "quota_used_date": user.quota_used_date.strftime("%Y-%m-%d") if user.quota_used_date else None,
        "window_max": settings.RATE_WINDOW_MAX,
        "window_seconds": settings.RATE_WINDOW_SECONDS,
    }


def consume_check_quota(db: Session, user: User, scope: str) -> dict:
    today = date.today()
    if user.quota_used_date != today:
        user.quota_used_date = today
        user.quota_used = 0
    if not rate_limit_allow(user.id):
        raise AppError(ErrorCode.RATE_LIMITED, detail={"retry_after": settings.RATE_WINDOW_SECONDS})
    if user.quota_used >= user.daily_check_quota:
        log_event(
            "CHECK_QUOTA_REJECTED",
            user=user.email,
            used=user.quota_used,
            quota=user.daily_check_quota,
        )
        raise AppError(
            ErrorCode.QUOTA_EXHAUSTED,
            detail={
                "quota": user.daily_check_quota,
                "used": user.quota_used,
                "retry_after": 3600,
            },
        )
    if not acquire_check_lock(scope):
        log_event("CHECK_LOCKED", user=user.email, scope=scope)
        raise AppError(ErrorCode.CHECK_RUNNING, detail={"scope": scope})
    user.quota_used += 1
    db.commit()
    return quota_snapshot(user)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis sliding window on state-changing requests; 429 carries retry_after."""

    async def dispatch(self, request, call_next):
        path = request.url.path.rstrip("/") or "/"
        if request.method in RATE_LIMIT_WRITE_METHODS and not any(
            path.endswith(bypass) for bypass in RATE_LIMIT_BYPASS
        ):
            claims = getattr(request.state, "user_claims", None) or {}
            user_id = claims.get("sub")
            if user_id and not rate_limit_allow(int(user_id)):
                from starlette.responses import JSONResponse

                from app.schemas.common import error_envelope

                return JSONResponse(
                    status_code=429,
                    content=error_envelope(
                        ErrorCode.RATE_LIMITED.value,
                        "请求过于频繁",
                        getattr(request.state, "request_id", None),
                        {"retry_after": settings.RATE_WINDOW_SECONDS},
                    ),
                )
        return await call_next(request)
