from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class OwnerTeam(Base):
    __tablename__ = "owner_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    domain: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    lead_name: Mapped[str] = mapped_column(String(80), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    sla_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    members = relationship("User", back_populates="team")
    metrics = relationship("MetricDefinition", back_populates="owner_team")
    versions = relationship("MetricVersion", back_populates="team")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OwnerTeam {self.code} domain={self.domain}>"
