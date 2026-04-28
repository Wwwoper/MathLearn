from datetime import datetime
from typing import Optional, Dict, Any
from app.services.mode_config import get_mode_config
from app.models.sr_card import SRCard
from app.models.user import User


class ReviewService:
    """Сервис для обработки ответов пользователя и расчета XP"""

    @staticmethod
    def process_answer(
        user: User,
        card: SRCard,
        is_correct: bool,
        response_time_sec: float,
        mode: str = "classic"
    ) -> Dict[str, Any]:
        """
        Обрабатывает ответ пользователя и возвращает результат с начисленным XP.
        
        Args:
            user: Модель пользователя
            card: Карточка с вопросом
            is_correct: Правильность ответа
            response_time_sec: Время ответа в секундах
            mode: Режим обучения
            
        Returns:
            Словарь с результатами: xp_gained, speed_bonus_xp, is_timeout, new_streak
        """
        mode_config = get_mode_config(mode)
        base_xp = mode_config.get("base_xp", 10)
        
        result = {
            "is_correct": is_correct,
            "xp_gained": 0,
            "speed_bonus_xp": 0,
            "is_timeout": False,
            "streak_maintained": False
        }
        
        # Проверка тайм-аута для режима Sprinter (в режиме Zen таймеры отключены)
        if mode == "sprinter":
            time_limit = mode_config.get("time_limit_sec", 30)
            if response_time_sec > time_limit:
                result["is_timeout"] = True
                # В режиме спринтер просроченный ответ считается неверным
                is_correct = False
                result["is_correct"] = False
        # В режиме Zen таймеры игнорируются, timeout никогда не срабатывает
        elif mode == "zen":
            # Таймеры отключены, ответ всегда принимается независимо от времени
            pass
        
        if is_correct:
            result["streak_maintained"] = True
            total_xp = base_xp
            
            # Расчет бонуса за скорость для режима Sprinter
            if mode == "sprinter":
                speed_bonus = ReviewService._calculate_speed_bonus(
                    response_time_sec,
                    mode_config.get("time_limit_sec", 30),
                    base_xp
                )
                result["speed_bonus_xp"] = speed_bonus
                total_xp += speed_bonus
            
            # Применение множителя XP от серии побед (streak)
            # В режиме Zen серия не прерывается при ошибке, но множитель применяется всегда
            streak_multiplier = user.xp_multiplier if hasattr(user, 'xp_multiplier') else 1.0
            total_xp = int(total_xp * streak_multiplier)
            
            result["xp_gained"] = total_xp
        else:
            # В режиме Zen серия побед не прерывается при ошибке
            if mode == "zen":
                result["streak_maintained"] = True
        
        return result

    @staticmethod
    def _calculate_speed_bonus(response_time_sec: float, time_limit_sec: float, base_xp: int) -> int:
        """
        Рассчитывает бонус XP за скорость ответа.
        Чем быстрее ответ, тем выше бонус (до +50% от базового XP).
        
        Формула: bonus = base_xp * 0.5 * (1 - response_time / time_limit)
        """
        if time_limit_sec <= 0:
            return 0
            
        # Нормализуем время ответа (от 0 до 1, где 0 - мгновенный ответ)
        time_ratio = min(response_time_sec / time_limit_sec, 1.0)
        
        # Бонус от 50% (мгновенный ответ) до 0% (ответ на пределе времени)
        bonus_multiplier = 0.5 * (1.0 - time_ratio)
        
        speed_bonus = int(base_xp * bonus_multiplier)
        return max(0, speed_bonus)

    @staticmethod
    def evaluate_weak_spot(card: SRCard) -> float:
        """
        Оценивает, насколько карточка является "слабым местом".
        Возвращает приоритет (чем выше значение, тем важнее повторить).
        
        Учитывает:
        - Количество ошибок
        - Последний уровень уверенности
        - Время с последнего повторения
        """
        error_count = getattr(card, 'error_count', 0)
        confidence = getattr(card, 'confidence_level', 0)
        
        # Приоритет растет с количеством ошибок и падает с уверенностью
        priority = (error_count * 2) - (confidence * 0.5)
        
        return max(0, priority)
