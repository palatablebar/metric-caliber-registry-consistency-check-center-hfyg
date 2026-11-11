"""Shared response envelope."""
from app.utils.formatters import iso


def error_envelope(code: str, message: str, request_id: str | None, detail=None) -> dict:
    return {"code": code, "message": message, "detail": detail, "request_id": request_id}


__all__ = ["error_envelope", "iso"]
