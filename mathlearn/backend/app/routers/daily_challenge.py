"""API эндпоинты для Ежедневного вызова (Daily Challenge)."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.user import User
from app.models.daily_challenge import DailyChallenge
from app.services.daily_challenge import DailyChallengeService
from app.schemas.daily_challenge import (
    DailyChallengeResponse,
    DailyChallengeCreateResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    LeaderboardEntry,
    LeaderboardResponse,
)


router = APIRouter(prefix="/api/daily-challenge", tags=["daily-challenge"])


@router.get("", response_model=DailyChallengeResponse)
async def get_daily_challenge(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить текущий ежедневный вызов для пользователя.
    
    Если вызов ещё не сгенерирован на сегодня, он будет создан автоматически.
    """
    challenge = await DailyChallengeService.get_today_challenge(db, current_user.id)
    
    if not challenge:
        # Генерируем новый вызов
        challenge = await DailyChallengeService.generate_challenge(db, current_user.id)
    
    return DailyChallengeResponse(
        id=challenge.id,
        date=challenge.date,
        questions=challenge.questions,
        condition_type=challenge.condition_type,
        condition_value=challenge.condition_value,
        completed=challenge.completed,
        score=challenge.score,
        completed_at=challenge.completed_at,
    )


@router.post("/submit", response_model=SubmitAnswerResponse)
async def submit_daily_challenge_answer(
    request: SubmitAnswerRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Отправить ответ на ежедневный вызов.
    
    Принимает ID сессии дрill-а и ID вызова, оценивает результат
    и возвращает информацию о выполнении условия.
    """
    try:
        result = await DailyChallengeService.evaluate_challenge(
            session=db,
            drill_session_id=request.drill_session_id,
            challenge_id=request.challenge_id,
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to evaluate challenge"),
            )
        
        return SubmitAnswerResponse(
            condition_met=result["condition_met"],
            score=result["score"],
            points_earned=result["points_earned"],
            condition_type=result["condition_type"],
            condition_value=result["condition_value"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_daily_leaderboard(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить таблицу лидеров ежедневного вызова за сегодня.
    
    Возвращает топ пользователей по очкам, заработанным в ежедневных испытаниях.
    """
    from sqlalchemy import select, desc
    from app.models.weekly_challenge import WeeklyChallengeEntry
    
    today = date.today()
    week_start = DailyChallengeService._get_week_start(today)
    
    # Получаем записи за текущую неделю
    stmt = (
        select(WeeklyChallengeEntry)
        .where(WeeklyChallengeEntry.week_start == week_start)
        .order_by(desc(WeeklyChallengeEntry.total_points))
        .limit(10)
    )
    
    result = await db.execute(stmt)
    entries = result.scalars().all()
    
    leaderboard = []
    for idx, entry in enumerate(entries, start=1):
        user = await db.get(User, entry.user_id)
        leaderboard.append(
            LeaderboardEntry(
                rank=idx,
                user_id=entry.user_id,
                username=user.username if user else f"User_{entry.user_id}",
                total_points=entry.total_points,
                challenges_completed=entry.challenges_completed,
            )
        )
    
    return LeaderboardResponse(
        date=today,
        week_start=week_start,
        entries=leaderboard,
    )
