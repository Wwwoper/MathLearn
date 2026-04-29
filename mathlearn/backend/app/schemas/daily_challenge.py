"""Схемы для Ежедневного вызова (Daily Challenge)."""

from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional


class DailyChallengeResponse(BaseModel):
    """Ответ с информацией о ежедневном вызове."""
    
    id: int
    date: date
    questions: dict
    condition_type: str
    condition_value: float
    completed: bool
    score: Optional[float] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DailyChallengeCreateResponse(BaseModel):
    """Ответ при создании нового ежедневного вызова."""
    
    id: int
    date: date
    message: str = "Ежедневный вызов успешно создан"
    
    class Config:
        from_attributes = True


class SubmitAnswerRequest(BaseModel):
    """Запрос на отправку ответа для ежедневного вызова."""
    
    drill_session_id: int = Field(..., description="ID завершённой DrillSession")
    challenge_id: int = Field(..., description="ID DailyChallenge")


class SubmitAnswerResponse(BaseModel):
    """Ответ после оценки ежедневного вызова."""
    
    condition_met: bool = Field(..., description="Выполнено ли условие вызова")
    score: float = Field(..., description="Полученный результат (точность или время)")
    points_earned: int = Field(..., description="Заработанные очки для недельного челленджа")
    condition_type: str = Field(..., description="Тип условия (accuracy/speed_improvement)")
    condition_value: float = Field(..., description="Пороговое значение условия")


class LeaderboardEntry(BaseModel):
    """Запись в таблице лидеров."""
    
    rank: int
    user_id: int
    username: str
    total_points: int
    challenges_completed: int


class LeaderboardResponse(BaseModel):
    """Ответ с таблицей лидеров."""
    
    date: date
    week_start: date
    entries: list[LeaderboardEntry]
