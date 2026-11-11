from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class MetricVersion(Base):
    __tablename__ = "metric_versions"
    __table_args__ = (UniqueConstraint("metric_id", "version_no", name="uq_metric_version_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metric_definitions.id"), nullable=False, index=True)
    # the team that authored this version (a metric key can be re-implemented by other teams)
    team_id: Mapped[int] = mapped_column(ForeignKey("owner_teams.id"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    dsl_text: Mapped[str] = mapped_column(Text, nullable=False)
    agg: Mapped[str | None] = mapped_column(String(32), nullable=True)
    measure: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_table: Mapped[str | None] = mapped_column(String(120), nullable=True)
    filters_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    window: Mapped[str | None] = mapped_column(String(32), nullable=True)
    grain: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    parse_status: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    metric = relationship("MetricDefinition", back_populates="versions")
    team = relationship("OwnerTeam", back_populates="versions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MetricVersion metric={self.metric_id} v{self.version_no}>"
