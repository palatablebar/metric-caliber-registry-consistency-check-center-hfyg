from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(190), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # role: admin | owner | analyst  (see app/constants/roles.py)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="analyst")
    team_id: Mapped[int | None] = mapped_column(ForeignKey("owner_teams.id"), nullable=True)
    daily_check_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    quota_used_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quota_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    team = relationship("OwnerTeam", back_populates="members")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email} role={self.role}>"
