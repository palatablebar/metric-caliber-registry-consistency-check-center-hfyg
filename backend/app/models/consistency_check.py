from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class ConsistencyCheck(Base):
    __tablename__ = "consistency_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_no: Mapped[str] = mapped_column(String(48), unique=True, nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="all")
    # pending | running | completed | failed
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    triggered_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metrics_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    versions_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflict_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consistency_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    findings = relationship("ConflictFinding", back_populates="check", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ConsistencyCheck {self.batch_no} {self.status}>"
