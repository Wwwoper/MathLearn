"""Схемы для интервального повторения (SR)."""

from datetime import datetime
from pydantic import BaseModel, Field


class SRCardResponse(BaseModel):
    """Схема ответа с данными карточки интервального повторения."""

    id: int
    user_id: int
    factor_a: int
    factor_b: int
    ease_factor: float
    interval_days: int
    next_review_at: datetime | None
    repetitions: int
    lapses: int

    class Config:
        from_attributes = True


class SRReviewRequest(BaseModel):
    """Схема запроса на отзыв о карточке."""

    card_id: int
    rating: int = Field(..., ge=1, le=4)  # 1-4 (Не знал, Трудно, Знал, Легко)
    response_time_ms: int = Field(..., ge=0)


class SRProgressResponse(BaseModel):
    """Схема ответа с прогрессом по матрице 10x10."""

    matrix: list[list[dict]]
    # matrix[a-1][b-1] содержит информацию о карточке a×b

    class Config:
        from_attributes = True
