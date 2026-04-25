"""Роуты для авторизации."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.core.security import get_password_hash, verify_password, create_token_pair, decode_token, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.models.user import User
from app.models.sr_card import SRCard
from app.core.deps import get_current_user, http_bearer
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["Авторизация"])


async def create_initial_sr_cards(db: AsyncSession, user_id: int):
    """Создание 100 начальных SR-карточек для пользователя (таблица умножения 1-10)."""
    cards = []
    for a in range(1, 11):
        for b in range(1, 11):
            card = SRCard(
                user_id=user_id,
                factor_a=a,
                factor_b=b,
                ease_factor=2.5,
                interval_days=0,
                repetitions=0,
                lapses=0,
            )
            cards.append(card)
    
    db.add_all(cards)
    await db.commit()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest, db: AsyncSession = Depends(get_async_session)):
    """Регистрация нового пользователя."""
    # Проверка существования пользователя с таким email
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )
    
    # Создание нового пользователя
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Создание 100 SR-карточек для нового пользователя
    await create_initial_sr_cards(db, new_user.id)
    
    # Создание пары токенов
    access_token, refresh_token = create_token_pair(new_user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": new_user,
    }


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_async_session)):
    """Вход пользователя и получение токенов."""
    # Поиск пользователя по email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создание пары токенов
    access_token, refresh_token = create_token_pair(user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(refresh_token: str, db: AsyncSession = Depends(get_async_session)):
    """Обновление токена доступа."""
    # Декодирование refresh токена
    payload = decode_token(refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или истекший refresh токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверка типа токена
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный тип токена",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Получение user_id
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен: отсутствует user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверка существования пользователя
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создание новой пары токенов
    new_access_token, new_refresh_token = create_token_pair(user.id)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    """Выход пользователя и инвалидация refresh токена в Redis."""
    # В реальной реализации здесь нужно добавить токен в blacklist в Redis
    # Для простоты пока просто возвращаем успех
    return {"message": "Успешный выход"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе."""
    return current_user
