"""Планировщик задач (cron jobs)."""

from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.core.database import get_async_session
from app.models.user import User
from app.models.sr_review import SRReview

logger = logging.getLogger(__name__)


async def check_and_reset_streaks():
    """Ежедневная проверка streak всех пользователей.
    
    Если пользователь не выполнил ни одного отзыва за текущий день,
    его current_streak обнуляется.
    """
    logger.info("Запуск проверки streak...")
    
    # Получаем сессию БД
    session_generator = get_async_session()
    db: AsyncSession = await session_generator.asend(None)
    
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Получаем всех пользователей
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        reset_count = 0
        
        for user in users:
            # Проверяем, были ли у пользователя отзывы сегодня
            stmt = (
                select(func.count(SRReview.id))
                .where(SRReview.user_id == user.id)
                .where(SRReview.reviewed_at >= today_start)
            )
            review_result = await db.execute(stmt)
            reviews_today = review_result.scalar() or 0
            
            # Если отзывов не было и streak > 0, сбрасываем
            if reviews_today == 0 and user.current_streak > 0:
                user.current_streak = 0
                reset_count += 1
                logger.info(f"Сброшен streak у пользователя {user.id} ({user.email})")
        
        await db.commit()
        logger.info(f"Проверка streak завершена. Сброшено: {reset_count}")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке streak: {e}")
        await db.rollback()
    finally:
        await db.close()


# Глобальный экземпляр планировщика
scheduler = AsyncIOScheduler()


def start_scheduler():
    """Запустить планировщик задач."""
    # Ежедневная проверка streak в 23:59
    scheduler.add_job(
        check_and_reset_streaks,
        trigger=CronTrigger(hour=23, minute=59),
        id="daily_streak_check",
        name="Daily streak check",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Планировщик запущен. Задачи: daily_streak_check (23:59)")


def shutdown_scheduler():
    """Остановить планировщик."""
    scheduler.shutdown()
    logger.info("Планировщик остановлен")
