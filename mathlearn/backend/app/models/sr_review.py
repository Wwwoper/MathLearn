"""Модель отзыва на карточку интервального повторения."""

from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SRReview(Base):
    """Модель отзыва/ответа на карточку интервального повторения."""

    __tablename__ = "sr_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    card_id: Mapped[int] = mapped_column(Integer, ForeignKey("sr_cards.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-4 (Не знал, Трудно, Знал, Легко)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи
    card: Mapped["SRCard"] = relationship("SRCard", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="sr_reviews")

    def __repr__(self) -> str:
        return f"<SRReview(id={self.id}, card_id={self.card_id}, rating={self.rating})>"
