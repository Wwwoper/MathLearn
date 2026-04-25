"""Схемы для AI Tutor."""

from datetime import datetime
from pydantic import BaseModel, Field


class LessonPlanDay(BaseModel):
    """Схема плана урока на один день."""

    day: int = Field(..., ge=1, le=7)
    focus_factors: list[tuple[int, int]]  # Список пар (a, b) для фокуса
    mode: str  # "sr" или "drill"
    explanation: str  # Объяснение почему выбран этот план


class AIRecommendationResponse(BaseModel):
    """Схема ответа с рекомендацией от ИИ."""

    id: int
    user_id: int
    lesson_plan: list[LessonPlanDay]
    reasoning: str
    model_name: str
    generated_at: datetime

    class Config:
        from_attributes = True


class AIStatusResponse(BaseModel):
    """Схема ответа со статусом AI сервиса."""

    ollama_available: bool
    model_name: str | None
    last_recommendation_at: datetime | None
