"""Роуты для интервального повторения (SR)."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.user import User
from app.models.sr_card import SRCard
from app.models.sr_review import SRReview
from app.schemas.sr import SRCardResponse, SRReviewRequest, SRProgressResponse
from app.services.sr_engine import calculate_next_review

router = APIRouter(prefix="/sr", tags=["Интервальное повторение"])


@router.get("/queue", response_model=list[SRCardResponse])
async def get_sr_queue(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Получить карточки для повторения.
    
    Возвращает карточки, где next_review_at <= now(), 
    отсортированные по ease_factor ASC (сначала самые лёгкие для забывания).
    """
    now = datetime.now()
    
    result = await db.execute(
        select(SRCard)
        .where(SRCard.user_id == current_user.id)
        .where(SRCard.next_review_at <= now)
        .order_by(SRCard.ease_factor.asc())
    )
    cards = result.scalars().all()
    
    return cards


@router.post("/review")
async def submit_review(
    review_data: SRReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Обработать отзыв о карточке.
    
    Принимает {card_id, rating, response_time_ms}, вызывает SM-2,
    обновляет карточку и сохраняет отзыв.
    """
    # Проверка существования карточки и принадлежности пользователю
    result = await db.execute(
        select(SRCard)
        .where(SRCard.id == review_data.card_id)
        .where(SRCard.user_id == current_user.id)
    )
    card = result.scalar_one_or_none()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карточка не найдена",
        )
    
    # Расчёт новых параметров по алгоритму SM-2
    ease_factor_new, interval_days_new, next_review_at, repetitions_new = calculate_next_review(
        card, review_data.rating
    )
    
    # Обновление карточки
    card.ease_factor = ease_factor_new
    card.interval_days = interval_days_new
    card.next_review_at = next_review_at
    card.repetitions = repetitions_new
    
    # Увеличение lapses при плохом ответе
    if review_data.rating < 2:
        card.lapses += 1
    
    # Сохранение отзыва
    review = SRReview(
        card_id=card.id,
        user_id=current_user.id,
        rating=review_data.rating,
        response_time_ms=review_data.response_time_ms,
    )
    db.add(review)
    
    await db.commit()
    await db.refresh(card)
    
    return {"message": "Отзыв сохранён", "card": SRCardResponse.model_validate(card)}


@router.get("/progress", response_model=SRProgressResponse)
async def get_sr_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Получить матрицу прогресса 10×10.
    
    Возвращает состояние каждой карточки таблицы умножения.
    matrix[a-1][b-1] содержит информацию о карточке a×b.
    """
    # Получение всех карточек пользователя
    result = await db.execute(
        select(SRCard)
        .where(SRCard.user_id == current_user.id)
        .order_by(SRCard.factor_a, SRCard.factor_b)
    )
    cards = result.scalars().all()
    
    # Создание словаря для быстрого доступа
    cards_dict = {(card.factor_a, card.factor_b): card for card in cards}
    
    # Построение матрицы 10×10
    matrix = []
    for a in range(1, 11):
        row = []
        for b in range(1, 11):
            card = cards_dict.get((a, b))
            if card:
                row.append({
                    "factor_a": card.factor_a,
                    "factor_b": card.factor_b,
                    "ease_factor": card.ease_factor,
                    "interval_days": card.interval_days,
                    "repetitions": card.repetitions,
                    "lapses": card.lapses,
                    "next_review_at": card.next_review_at,
                })
            else:
                row.append({
                    "factor_a": a,
                    "factor_b": b,
                    "ease_factor": None,
                    "interval_days": None,
                    "repetitions": None,
                    "lapses": None,
                    "next_review_at": None,
                })
        matrix.append(row)
    
    return {"matrix": matrix}


@router.get("/today")
async def get_today_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Получить статистику на сегодня.
    
    Возвращает {due_count, completed_today}:
    - due_count: количество карточек, ожидающих повторения сегодня
    - completed_today: количество выполненных отзывов сегодня
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Количество карточек, ожидающих повторения
    due_result = await db.execute(
        select(func.count(SRCard.id))
        .where(SRCard.user_id == current_user.id)
        .where(SRCard.next_review_at <= now)
    )
    due_count = due_result.scalar() or 0
    
    # Количество выполненных отзывов сегодня
    completed_result = await db.execute(
        select(func.count(SRReview.id))
        .where(SRReview.user_id == current_user.id)
        .where(SRReview.reviewed_at >= today_start)
        .where(SRReview.reviewed_at < today_end)
    )
    completed_today = completed_result.scalar() or 0
    
    return {
        "due_count": due_count,
        "completed_today": completed_today,
    }
