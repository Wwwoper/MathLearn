"""Схемы для авторизации."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    """Схема запроса на регистрацию пользователя."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    """Схема запроса на вход пользователя."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Схема ответа с токенами и данными пользователя."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None


class TokenPayload(BaseModel):
    """Схема содержимого токена."""

    sub: int  # user id
    exp: int  # expiration time
    type: str  # "access" or "refresh"
