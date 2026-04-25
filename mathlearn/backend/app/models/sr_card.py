"""Модель карточки интервального повторения (SR)."""

from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SRCard(Base):
    """Модель карточки для интервального повторения таблицы умножения."""

    __tablename__ = "sr_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    factor_a: Mapped[int] = mapped_column(Integer, nullable=False)
    factor_b: Mapped[int] = mapped_column(Integer, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="sr_cards")
    reviews: Mapped[list["SRReview"]] = relationship("SRReview", back_populates="card", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SRCard(id={self.id}, user_id={self.user_id}, {self.factor_a}x{self.factor_b})>"
