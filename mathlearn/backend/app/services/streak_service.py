from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.sr_card import SRCard


class StreakService:
    """Сервис для управления сериями побед (streak) и заморозками."""

    def __init__(self, db: Session):
        self.db = db

    def update_streak(self, user_id: int) -> Dict[str, Any]:
        """
        Обновляет серию побед пользователя после успешного ответа.
        
        :param user_id: ID пользователя
        :return: Статус серии (текущая серия, множитель XP)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        today = datetime.utcnow().date()
        last_activity = user.last_activity_date

        if last_activity is None:
            # Первый вход/активность
            user.current_streak = 1
            user.best_streak = 1
        elif last_activity < today - timedelta(days=1):
            # Пропуск дня - серия сбрасывается
            user.current_streak = 1
        elif last_activity == today - timedelta(days=1):
            # Вчерашняя активность - увеличиваем серию
            user.current_streak += 1
            if user.current_streak > user.best_streak:
                user.best_streak = user.current_streak
        # Если last_activity == today, серия уже учтена за сегодня

        user.last_activity_date = today
        user.xp_multiplier = self._calculate_xp_multiplier(user.current_streak)

        self.db.commit()
        self.db.refresh(user)

        return {
            "current_streak": user.current_streak,
            "best_streak": user.best_streak,
            "xp_multiplier": user.xp_multiplier,
            "streak_freeze_count": user.streak_freeze_count
        }

    def use_freeze(self, user_id: int) -> Dict[str, Any]:
        """
        Использует заморозку серии для сохранения текущего streak при пропуске дня.
        
        :param user_id: ID пользователя
        :return: Обновленное количество заморозок
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        if user.streak_freeze_count <= 0:
            raise ValueError("No streak freezes available")

        user.streak_freeze_count -= 1
        self.db.commit()
        self.db.refresh(user)

        return {
            "streak_freeze_count": user.streak_freeze_count,
            "current_streak": user.current_streak
        }

    def get_streak_status(self, user_id: int) -> Dict[str, Any]:
        """
        Возвращает текущий статус серии побед пользователя.
        
        :param user_id: ID пользователя
        :return: Информация о серии
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        return {
            "current_streak": user.current_streak,
            "best_streak": user.best_streak,
            "xp_multiplier": user.xp_multiplier,
            "streak_freeze_count": user.streak_freeze_count,
            "last_activity_date": user.last_activity_date.isoformat() if user.last_activity_date else None
        }

    def _calculate_xp_multiplier(self, streak: int) -> float:
        """
        Рассчитывает множитель XP на основе длины серии.
        Максимальный множитель: 2.0x при 30+ днях.
        
        :param streak: Длина серии
        :return: Множитель XP (от 1.0 до 2.0)
        """
        if streak <= 0:
            return 1.0
        
        # Линейный рост от 1.0 до 2.0 за 30 дней
        multiplier = 1.0 + (min(streak, 30) / 30.0)
        return round(multiplier, 2)

    def check_streak_loss(self, user_id: int) -> bool:
        """
        Проверяет, потерял ли пользователь серию из-за пропуска дня.
        Если есть заморозка - автоматически применяет её.
        
        :param user_id: ID пользователя
        :return: True если серия сохранена (или была активна), False если сброшена
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        today = datetime.utcnow().date()
        last_activity = user.last_activity_date

        if last_activity is None:
            return True  # Нет активности, но и потери нет

        # Если прошло больше 1 дня с последней активности
        if last_activity < today - timedelta(days=1):
            if user.streak_freeze_count > 0:
                # Автоматически используем заморозку
                self.use_freeze(user_id)
                # Восстанавливаем last_activity на вчерашний день чтобы серия не сбросилась
                user.last_activity_date = today - timedelta(days=1)
                self.db.commit()
                return True
            else:
                # Сбрасываем серию
                user.current_streak = 0
                user.xp_multiplier = 1.0
                self.db.commit()
                return False

        return True
