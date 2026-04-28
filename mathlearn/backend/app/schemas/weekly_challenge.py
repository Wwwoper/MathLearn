from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class WeeklyChallengeStatusResponse(BaseModel):
    """Ответ со статусом недельного челленджа"""
    current_points: int = Field(..., description="Текущие очки пользователя")
    target_points: int = Field(..., description="Целевое количество очков на неделю")
    week_start: datetime = Field(..., description="Начало текущей недели")
    week_end: datetime = Field(..., description="Конец текущей недели")
    completed_tiers: List[int] = Field(default_factory=list, description="ID полученных наград")
    is_active: bool = Field(default=True, description="Активен ли челлендж")


class WeeklyRewardResponse(BaseModel):
    """Ответ с информацией о награде"""
    id: int = Field(..., description="ID награды")
    name: str = Field(..., description="Название награды")
    description: str = Field(..., description="Описание награды")
    required_points: int = Field(..., description="Необходимое количество очков для получения")
    reward_type: str = Field(..., description="Тип награды (xp, coins, freeze, etc.)")
    reward_value: int = Field(..., description="Значение награды")
    is_unlocked: bool = Field(..., description="Разблокирована ли награда")
    is_claimed: bool = Field(..., description="Получена ли уже эта награда")


class ClaimRewardRequest(BaseModel):
    """Запрос на получение награды"""
    reward_id: int = Field(..., description="ID награды для получения")


class ClaimRewardResponse(BaseModel):
    """Ответ после получения награды"""
    success: bool = Field(..., description="Успешно ли получена награда")
    message: str = Field(..., description="Сообщение о результате")
    reward_type: str = Field(..., description="Тип полученной награды")
    reward_value: int = Field(..., description="Значение полученной награды")
