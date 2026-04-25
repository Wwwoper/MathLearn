"""API для статистики."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.user import User
from app.models.sr_card import SRCard
from app.models.sr_review import SRReview
from app.models.drill_session import DrillSession
from app.schemas.stats import (
    HeatmapResponse,
    HeatmapCell,
    SpeedResponse,
    SpeedDataPoint,
    StreakResponse,
    AchievementsResponse,
    AchievementResponse,
)
from app.services.gamification import check_achievements

router = APIRouter(prefix="/stats", tags=["Статистика"])


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> HeatmapResponse:
    """Получить матрицу 10x10 с количеством ошибок, средним временем ответа и точностью.
    
    Возвращает heatmap, где matrix[a-1][b-1] содержит статистику по карточке a×b:
    - error_count: количество ошибок (rating < 2)
    - avg_time_ms: среднее время ответа
    - accuracy: процент правильных ответов
    """
    # Получение всех отзывов пользователя сгруппированных по карточкам
    result = await db.execute(
        select(
            SRCard.factor_a,
            SRCard.factor_b,
            func.count(SRReview.id).label("total_reviews"),
            func.sum(func.case((SRReview.rating < 2, 1), else_=0)).label("error_count"),
            func.avg(SRReview.response_time_ms).label("avg_time_ms"),
        )
        .join(SRReview, SRCard.id == SRReview.card_id)
        .where(SRCard.user_id == current_user.id)
        .group_by(SRCard.factor_a, SRCard.factor_b)
    )
    reviews_data = result.all()
    
    # Создание словаря для быстрого доступа
    stats_dict = {}
    for row in reviews_data:
        key = (row.factor_a, row.factor_b)
        total = row.total_reviews or 0
        errors = row.error_count or 0
        avg_time = int(row.avg_time_ms) if row.avg_time_ms else 0
        accuracy = ((total - errors) / total * 100) if total > 0 else 0.0
        
        stats_dict[key] = {
            "error_count": errors,
            "avg_time_ms": avg_time,
            "accuracy": round(accuracy, 2),
        }
    
    # Построение матрицы 10×10
    matrix = []
    for a in range(1, 11):
        row = []
        for b in range(1, 11):
            key = (a, b)
            if key in stats_dict:
                cell = HeatmapCell(
                    factor_a=a,
                    factor_b=b,
                    error_count=stats_dict[key]["error_count"],
                    avg_time_ms=stats_dict[key]["avg_time_ms"],
                    accuracy=stats_dict[key]["accuracy"],
                )
            else:
                cell = HeatmapCell(
                    factor_a=a,
                    factor_b=b,
                    error_count=0,
                    avg_time_ms=0,
                    accuracy=0.0,
                )
            row.append(cell)
        matrix.append(row)
    
    return HeatmapResponse(matrix=matrix)


@router.get("/speed", response_model=SpeedResponse)
async def get_speed_stats(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> SpeedResponse:
    """Получить динамику скорости ответов по дням.
    
    Args:
        days: Количество дней для анализа (по умолчанию 30, макс 365)
    
    Returns:
        Список точек данных с датой, средним временем ответа и точностью за каждый день.
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Группировка отзывов по дням
    result = await db.execute(
        select(
            func.date(SRReview.reviewed_at).label("review_date"),
            func.count(SRReview.id).label("total_reviews"),
            func.sum(func.case((SRReview.rating >= 2, 1), else_=0)).label("correct_reviews"),
            func.avg(SRReview.response_time_ms).label("avg_response_ms"),
        )
        .join(SRCard, SRReview.card_id == SRCard.id)
        .where(SRCard.user_id == current_user.id)
        .where(SRReview.reviewed_at >= start_date)
        .group_by(func.date(SRReview.reviewed_at))
        .order_by(func.date(SRReview.reviewed_at))
    )
    daily_stats = result.all()
    
    data_points = []
    for row in daily_stats:
        accuracy = (row.correct_reviews / row.total_reviews * 100) if row.total_reviews > 0 else 0.0
        data_points.append(
            SpeedDataPoint(
                date=datetime.combine(row.review_date, datetime.min.time(), tzinfo=timezone.utc),
                avg_response_ms=int(row.avg_response_ms) if row.avg_response_ms else 0,
                accuracy=round(accuracy, 2),
            )
        )
    
    return SpeedResponse(data_points=data_points, days=days)


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> StreakResponse:
    """Получить информацию о текущей и максимальной сериях дней подряд.
    
    Returns:
        current_streak: текущая серия дней подряд
        max_streak: максимальная серия дней подряд за всё время
    """
    return StreakResponse(
        current_streak=current_user.current_streak,
        max_streak=current_user.max_streak,
    )


@router.get("/achievements", response_model=AchievementsResponse)
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> AchievementsResponse:
    """Получить список достижений с флагом разблокировки.
    
    Returns:
        Список всех достижений с информацией о том, разблокировано ли каждое.
    """
    # Определение всех возможных достижений
    all_achievements = [
        {"id": 1, "name": "Новичок", "description": "Достичь уровня 5"},
        {"id": 2, "name": "Средний уровень", "description": "Достичь уровня 10"},
        {"id": 3, "name": "Продвинутый", "description": "Достичь уровня 20"},
        {"id": 4, "name": "Эксперт", "description": "Достичь уровня 50"},
        {"id": 5, "name": "Мастер", "description": "Достичь уровня 100"},
        {"id": 6, "name": "Недельный воин", "description": "Серия 7 дней подряд"},
        {"id": 7, "name": "Месячный мастер", "description": "Серия 30 дней подряд"},
        {"id": 8, "name": "Чемпион века", "description": "Серия 100 дней подряд"},
        {"id": 9, "name": "Легенда года", "description": "Серия 365 дней подряд"},
        {"id": 10, "name": "Первая сотня", "description": "Выполнить 100 повторений"},
        {"id": 11, "name": "Преданный", "description": "Выполнить 500 повторений"},
        {"id": 12, "name": "Настойчивый", "description": "Выполнить 1000 повторений"},
        {"id": 13, "name": "Легендарный", "description": "Выполнить 5000 повторений"},
    ]
    
    # Получение разблокированных достижений
    unlocked_ids = await check_achievements(db, current_user.id)
    
    # Маппинг ID достижений на их ключи
    achievement_keys = {
        1: "novice",
        2: "intermediate",
        3: "advanced",
        4: "expert",
        5: "master",
        6: "week_warrior",
        7: "month_master",
        8: "century_champion",
        9: "year_legend",
        10: "first_hundred",
        11: "dedicated",
        12: "persistent",
        13: "legendary",
    }
    
    achievements_list = []
    for ach in all_achievements:
        key = achievement_keys.get(ach["id"], "")
        unlocked = key in unlocked_ids
        
        # Для разблокированных достижений пытаемся найти дату разблокировки
        unlocked_at = None
        if unlocked:
            # Упрощённо: если разблокировано, считаем датой последнее активное действие
            unlocked_at = current_user.last_active_at
        
        achievements_list.append(
            AchievementResponse(
                id=ach["id"],
                name=ach["name"],
                description=ach["description"],
                unlocked=unlocked,
                unlocked_at=unlocked_at,
            )
        )
    
    return AchievementsResponse(achievements=achievements_list)
