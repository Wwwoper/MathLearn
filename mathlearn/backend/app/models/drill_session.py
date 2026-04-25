"""Модель сессии тренировки (drill)."""

from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DrillSession(Base):
    """Модель сессии тренировки таблицы умножения."""

    __tablename__ = "drill_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="drill_sessions")

    def __repr__(self) -> str:
        return f"<DrillSession(id={self.id}, user_id={self.user_id})>"
