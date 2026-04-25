"""Схемы для пользователя."""

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя."""

    id: int
    name: str
    email: str
    xp: int = 0
    level: int = 1
    current_streak: int = 0
    max_streak: int = 0

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Схема запроса на обновление данных пользователя."""

    name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
