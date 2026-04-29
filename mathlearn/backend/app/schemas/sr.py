"""Схемы для интервального повторения (SR)."""

from datetime import datetime
from pydantic import BaseModel, Field


class SRCardResponse(BaseModel):
    """Схема ответа с данными карточки интервального повторения."""

    id: int
    user_id: int
    factor_a: int
    factor_b: int
    answer: int  # Вычисляемое поле для удобства фронтенда
    ease_factor: float
    interval_days: int
    next_review_at: datetime | None
    repetitions: int
    lapses: int
    locked: bool = False
    hints_remaining: int = 3

    class Config:
        from_attributes = True


class SRReviewRequest(BaseModel):
    """Схема запроса на отзыв о карточке."""

    card_id: int
    rating: int = Field(..., ge=1, le=5)  # 1-5 (😠, 😕, 😐, 🙂, 🤩)
    response_time_ms: int = Field(..., ge=0)


class SRProgressResponse(BaseModel):
    """Схема ответа с прогрессом по матрице 10x10."""

    matrix: list[list[dict]]
    # matrix[a-1][b-1] содержит информацию о карточке a×b

    class Config:
        from_attributes = True
