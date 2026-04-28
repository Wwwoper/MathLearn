"""Модель еженедельного испытания (Weekly Challenge)."""

from datetime import date
from sqlalchemy import Integer, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WeeklyChallengeEntry(Base):
    """Модель записи еженедельного испытания для режима Fighter."""

    __tablename__ = "weekly_challenge_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    challenges_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="weekly_challenge_entries")

    # Индексы
    __table_args__ = (
        Index("idx_weekly_entries_user_week", "user_id", "week_start"),
    )

    def __repr__(self) -> str:
        return f"<WeeklyChallengeEntry(id={self.id}, user_id={self.user_id}, week_start={self.week_start})>"
