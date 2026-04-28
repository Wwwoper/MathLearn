"""Модель ежедневного испытания (Daily Challenge)."""

from datetime import date, datetime
from sqlalchemy import Integer, Float, Boolean, Date, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DailyChallenge(Base):
    """Модель ежедневного испытания для режима Fighter."""

    __tablename__ = "daily_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    questions: Mapped[dict] = mapped_column(JSON, nullable=False)
    condition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition_value: Mapped[float] = mapped_column(Float, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="daily_challenges")

    def __repr__(self) -> str:
        return f"<DailyChallenge(id={self.id}, user_id={self.user_id}, date={self.date})>"
