"""Роуты для управления режимом обучения и профилем пользователя."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, LearningModeUpdateRequest
from app.services.mode_config import get_mode_config, is_mode_valid

router = APIRouter(prefix="/profile", tags=["Профиль и режимы обучения"])


@router.get("/mode", response_model=dict)
async def get_learning_mode(current_user: User = Depends(get_current_user)):
    """Получение текущего режима обучения пользователя."""
    return {
        "mode": current_user.learning_mode,
        "xp_multiplier": current_user.xp_multiplier,
        "config": get_mode_config(current_user.learning_mode)
    }


@router.post("/mode", response_model=UserResponse)
async def set_learning_mode(
    mode_data: LearningModeUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Установка режима обучения пользователя."""
    # Проверка валидности режима
    if not is_mode_valid(mode_data.mode):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный режим обучения. Доступные режимы: classic, sprinter, weak_spots, streak_hunter, fighter, zen"
        )
    
    # Обновление режима в БД
    current_user.learning_mode = mode_data.mode
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Получение полного профиля пользователя."""
    return current_user
