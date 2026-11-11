"""Offset pagination over SQLAlchemy 2.0 selects."""
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

MAX_PAGE_SIZE = 200


def page_args(page: int | None, page_size: int | None) -> tuple[int, int]:
    page = max(1, int(page or 1))
    page_size = min(MAX_PAGE_SIZE, max(1, int(page_size or 20)))
    return page, page_size


def paginate(db: Session, stmt: Select, page: int, page_size: int) -> tuple[list[Any], int]:
    total = int(db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
    rows = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return list(rows), total
