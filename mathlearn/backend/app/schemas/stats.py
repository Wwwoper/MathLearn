"""Схемы для статистики."""

from datetime import datetime
from pydantic import BaseModel


class HeatmapCell(BaseModel):
    """Схема ячейки heatmap."""

    factor_a: int
    factor_b: int
    error_count: int = 0
    avg_time_ms: int = 0
    accuracy: float = 0.0


class HeatmapResponse(BaseModel):
    """Схема ответа с heatmap ошибок (матрица 10x10)."""

    matrix: list[list[HeatmapCell]]


class SpeedDataPoint(BaseModel):
    """Схема точки данных скорости."""

    date: datetime
    avg_response_ms: int
    accuracy: float


class SpeedResponse(BaseModel):
    """Схема ответа с динамикой скорости ответов."""

    data_points: list[SpeedDataPoint]
    days: int


class StreakResponse(BaseModel):
    """Схема ответа с данными о streak."""

    current_streak: int
    max_streak: int


class AchievementResponse(BaseModel):
    """Схема достижения."""

    id: int
    name: str
    description: str
    unlocked: bool
    unlocked_at: datetime | None


class AchievementsResponse(BaseModel):
    """Схема ответа со списком достижений."""

    achievements: list[AchievementResponse]
