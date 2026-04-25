"""Модель рекомендации от ИИ."""

from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class AIRecommendation(Base):
    """Модель рекомендации по обучению от ИИ."""

    __tablename__ = "ai_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lesson_plan: Mapped[dict] = mapped_column(JSONB, nullable=False)  # План урока в формате JSON
    reasoning: Mapped[str] = mapped_column(Text, nullable=True)  # Объяснение рекомендации
    model_name: Mapped[str] = mapped_column(String(100), nullable=True)  # Название модели ИИ
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="ai_recommendations")

    def __repr__(self) -> str:
        return f"<AIRecommendation(id={self.id}, user_id={self.user_id})>"
