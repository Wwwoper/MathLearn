"""Сервис геймификации."""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.sr_review import SRReview


def get_level(xp: int) -> int:
    """Вычислить уровень по XP.
    
    Формула: level = int((xp / 100) ** (1 / 1.5)) + 1
    """
    return int((xp / 100) ** (1 / 1.5)) + 1


async def award_xp(session: AsyncSession, user_id: int, action: str) -> int:
    """Начислить XP за действие.
    
    Args:
        session: DB сессия
        user_id: ID пользователя
        action: Тип действия (review_correct, review_easy, drill_complete, etc.)
    
    Returns:
        Начисленное количество XP
    """
    # Таблица XP за действия
    xp_rewards = {
        "review_correct": 10,      # Правильный ответ в SR
        "review_easy": 15,         # Оценка 4 (легко)
        "review_hard": 5,          # Оценка 2 (трудно)
        "drill_complete": 50,      # Завершение drill-сессии
        "drill_perfect": 100,      # Drill-сессия без ошибок
        "streak_milestone": 200,   # Достижение рубежа streak (7, 30, 100 дней)
    }
    
    xp_amount = xp_rewards.get(action, 5)  # По умолчанию 5 XP
    
    user = await session.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    user.xp += xp_amount
    new_level = get_level(user.xp)
    
    # Повышение уровня
    if new_level > user.level:
        user.level = new_level
        # Можно добавить бонус за уровень
    
    await session.commit()
    await session.refresh(user)
    
    return xp_amount


async def update_streak(session: AsyncSession, user_id: int) -> tuple[int, bool]:
    """Обновить streak при завершении ежедневной очереди.
    
    Args:
        session: DB сессия
        user_id: ID пользователя
    
    Returns:
        Кортеж (текущий streak, был ли обновлён)
    """
    user = await session.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    now = datetime.now(timezone.utc)
    last_active = user.last_active_at
    
    streak_updated = False
    
    if last_active is None:
        # Первый раз
        user.current_streak = 1
        user.max_streak = 1
        streak_updated = True
    else:
        days_since_last = (now - last_active).days
        
        if days_since_last == 0:
            # Уже активен сегодня, streak не меняем
            pass
        elif days_since_last == 1:
            # Активен на следующий день — увеличиваем streak
            user.current_streak += 1
            streak_updated = True
        else:
            # Пропустил день — сбрасываем streak
            user.current_streak = 1
            streak_updated = True
    
    # Обновляем max_streak если нужно
    if user.current_streak > user.max_streak:
        user.max_streak = user.current_streak
    
    user.last_active_at = now
    
    await session.commit()
    await session.refresh(user)
    
    return user.current_streak, streak_updated


async def check_achievements(session: AsyncSession, user_id: int) -> list[str]:
    """Проверить и разблокировать ачивки.
    
    Args:
        session: DB сессия
        user_id: ID пользователя
    
    Returns:
        Список разблокированных ачивок
    """
    user = await session.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    unlocked = []
    
    # Ачивки по уровню
    level_achievements = {
        5: "novice",
        10: "intermediate",
        20: "advanced",
        50: "expert",
        100: "master",
    }
    
    for level, achievement in level_achievements.items():
        if user.level >= level:
            unlocked.append(achievement)
    
    # Ачивки по streak
    streak_achievements = {
        7: "week_warrior",
        30: "month_master",
        100: "century_champion",
        365: "year_legend",
    }
    
    for streak_days, achievement in streak_achievements.items():
        if user.current_streak >= streak_days or user.max_streak >= streak_days:
            unlocked.append(achievement)
    
    # Ачивки по количеству повторений
    stmt = select(SRReview).where(SRReview.user_id == user_id)
    result = await session.execute(stmt)
    reviews = result.scalars().all()
    total_reviews = len(reviews)
    
    review_achievements = {
        100: "first_hundred",
        500: "dedicated",
        1000: "persistent",
        5000: "legendary",
    }
    
    for count, achievement in review_achievements.items():
        if total_reviews >= count:
            unlocked.append(achievement)
    
    return list(set(unlocked))  # Убираем дубликаты


async def get_user_stats(session: AsyncSession, user_id: int) -> dict:
    """Получить полную статистику пользователя.
    
    Args:
        session: DB сессия
        user_id: ID пользователя
    
    Returns:
        Словарь со статистикой
    """
    user = await session.get(User, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    achievements = await check_achievements(session, user_id)
    
    return {
        "user_id": user.id,
        "xp": user.xp,
        "level": user.level,
        "current_streak": user.current_streak,
        "max_streak": user.max_streak,
        "achievements": achievements,
        "last_active_at": user.last_active_at,
    }
