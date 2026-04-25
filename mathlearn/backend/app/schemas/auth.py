"""Схемы для авторизации."""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Схема токена доступа."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Схема содержимого токена."""

    sub: int  # user id
    exp: int  # expiration time
    type: str  # "access" or "refresh"


class UserCreate(BaseModel):
    """Схема для регистрации пользователя."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    """Схема для входа пользователя."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


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
