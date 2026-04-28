from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.models.weekly_challenge import WeeklyChallengeEntry, WeeklyRewardTier
from app.services.weekly_challenge_service import WeeklyChallengeService
from app.schemas.weekly_challenge import (
    WeeklyChallengeStatusResponse,
    WeeklyRewardResponse,
    ClaimRewardRequest,
    ClaimRewardResponse
)
from app.core.security import get_current_user

router = APIRouter(prefix="/api/weekly-challenge", tags=["Weekly Challenge"])


@router.get("/status", response_model=WeeklyChallengeStatusResponse)
async def get_weekly_challenge_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить статус текущего недельного челленджа пользователя.
    Возвращает прогресс, текущие очки, цель и оставшееся время.
    """
    service = WeeklyChallengeService(db)
    status_data = service.get_user_status(current_user.id)
    
    if not status_data:
        # Если записи нет, создаем новую для текущей недели
        status_data = service.get_or_create_current_entry(current_user.id)
    
    return WeeklyChallengeStatusResponse(
        current_points=status_data.current_points,
        target_points=status_data.target_points,
        week_start=status_data.week_start,
        week_end=status_data.week_end,
        completed_tiers=status_data.completed_tiers,
        is_active=status_data.is_active
    )


@router.get("/rewards", response_model=List[WeeklyRewardResponse])
async def get_available_rewards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить список доступных наград за достижение пороговых значений очков.
    """
    service = WeeklyChallengeService(db)
    rewards = service.get_all_reward_tiers()
    
    # Получаем текущий прогресс пользователя
    user_entry = service.get_current_entry(current_user.id)
    current_points = user_entry.current_points if user_entry else 0
    
    result = []
    for reward in rewards:
        is_unlocked = current_points >= reward.required_points
        is_claimed = user_entry and service.is_reward_claimed(user_entry.id, reward.id) if user_entry else False
        
        result.append(WeeklyRewardResponse(
            id=reward.id,
            name=reward.name,
            description=reward.description,
            required_points=reward.required_points,
            reward_type=reward.reward_type,
            reward_value=reward.reward_value,
            is_unlocked=is_unlocked,
            is_claimed=is_claimed
        ))
    
    return result


@router.post("/claim", response_model=ClaimRewardResponse)
async def claim_reward(
    request: ClaimRewardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Забрать награду пользователем (с проверкой достижимости и одноразовости получения).
    """
    service = WeeklyChallengeService(db)
    
    # Получаем текущую запись пользователя
    user_entry = service.get_current_entry(current_user.id)
    if not user_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активный недельный челлендж не найден"
        )
    
    # Проверяем, может ли пользователь получить эту награду
    reward = db.query(WeeklyRewardTier).filter(WeeklyRewardTier.id == request.reward_id).first()
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Награда не найдена"
        )
    
    if user_entry.current_points < reward.required_points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно очков для получения этой награды"
        )
    
    # Проверяем, не была ли награда уже получена
    if service.is_reward_claimed(user_entry.id, reward.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Эта награда уже была получена"
        )
    
    # Забираем награду
    claimed_reward = service.claim_reward(user_entry.id, reward.id, current_user.id)
    
    return ClaimRewardResponse(
        success=True,
        message=f"Награда '{reward.name}' успешно получена!",
        reward_type=claimed_reward.reward_type,
        reward_value=claimed_reward.reward_value
    )
