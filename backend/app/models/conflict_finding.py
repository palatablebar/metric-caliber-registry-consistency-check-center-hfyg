from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class ConflictFinding(Base):
    __tablename__ = "conflict_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("consistency_checks.id"), nullable=False, index=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metric_definitions.id"), nullable=False, index=True)
    metric_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    # agg | measure | filter | window | grain | multi
    conflict_type: Mapped[str] = mapped_column(String(16), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    version_a_id: Mapped[int] = mapped_column(Integer, nullable=False)
    version_b_id: Mapped[int] = mapped_column(Integer, nullable=False)
    dimensions_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    evidence_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    impact_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # open | acknowledged | resolved
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    check = relationship("ConsistencyCheck", back_populates="findings")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ConflictFinding {self.metric_key} {self.severity}>"
