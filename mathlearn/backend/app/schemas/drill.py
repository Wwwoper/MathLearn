"""Схемы для Drill-режима."""

from datetime import datetime
from pydantic import BaseModel, Field


class DrillStartRequest(BaseModel):
    """Схема запроса на начало сессии тренировки."""

    tables: list[int] = Field(..., min_length=1)  # Какие таблицы умножения тренировать (2-9)
    limit: int = Field(..., ge=1, le=100)  # Количество вопросов
    time_limit_sec: int | None = Field(None, ge=10)  # Ограничение по времени в секундах


class DrillAnswerRequest(BaseModel):
    """Схема запроса на ответ в drill-сессии."""

    session_id: int
    answer: int = Field(..., ge=0)


class DrillResultResponse(BaseModel):
    """Схема ответа с результатами drill-сессии."""

    session_id: int
    total_questions: int
    correct_answers: int
    accuracy: float  # Процент правильных ответов
    avg_response_ms: int
    started_at: datetime
    ended_at: datetime | None

    class Config:
        from_attributes = True


class DrillQuestionResponse(BaseModel):
    """Схема ответа с вопросом для drill."""

    question_id: int
    factor_a: int
    factor_b: int
    session_id: int


class DrillAnswerResponse(BaseModel):
    """Схема ответа на submitted answer."""

    correct: bool
    correct_answer: int
    next_question: DrillQuestionResponse | None = None
    score: int
