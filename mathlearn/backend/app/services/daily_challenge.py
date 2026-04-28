"""Сервис ежедневных испытаний (Daily Challenge) для режима Fighter."""

from datetime import date, datetime, timezone
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.daily_challenge import DailyChallenge
from app.models.weekly_challenge import WeeklyChallengeEntry
from app.models.user import User
from app.models.sr_review import SRReview
from app.models.drill_session import DrillSession


class DailyChallengeService:
    """Сервис для управления ежедневными испытаниями."""

    @staticmethod
    async def generate_challenge(session: AsyncSession, user_id: int) -> DailyChallenge:
        """
        Сгенерировать ежедневное испытание для пользователя.

        Args:
            session: DB сессия
            user_id: ID пользователя

        Returns:
            Созданный объект DailyChallenge
        """
        user = await session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        today = date.today()

        # Проверка: есть ли уже испытание на сегодня
        stmt = select(DailyChallenge).where(
            DailyChallenge.user_id == user_id,
            DailyChallenge.date == today
        )
        result = await session.execute(stmt)
        existing_challenge = result.scalar_one_or_none()

        if existing_challenge:
            return existing_challenge

        # Генерация 20 вопросов случайным образом по всем таблицам (2-10)
        questions = []
        for _ in range(20):
            factor_a = random.randint(2, 10)
            factor_b = random.randint(2, 10)
            questions.append({"factor_a": factor_a, "factor_b": factor_b})

        # Определение типа условия и порогового значения
        # Получаем историю результатов пользователя
        stmt = select(SRReview).where(
            SRReview.user_id == user_id
        ).order_by(SRReview.reviewed_at.desc()).limit(50)
        result = await session.execute(stmt)
        recent_reviews = result.scalars().all()

        condition_type = "accuracy"
        condition_value = 70.0  # По умолчанию для первой сессии

        if recent_reviews:
            # Вычисляем среднюю точность
            correct_count = sum(1 for r in recent_reviews if r.rating >= 3)
            avg_accuracy = (correct_count / len(recent_reviews)) * 100 if recent_reviews else 0

            # Вычисляем среднее время ответа
            reviews_with_time = [r for r in recent_reviews if r.response_time_ms is not None]
            avg_response_ms = (
                sum(r.response_time_ms for r in reviews_with_time) / len(reviews_with_time)
                if reviews_with_time else None
            )

            # Выбираем тип условия случайно или на основе истории
            condition_choices = ["accuracy", "speed_improvement"]
            condition_type = random.choice(condition_choices)

            if condition_type == "accuracy":
                # Порог: средняя точность + 5%
                condition_value = min(avg_accuracy + 5.0, 95.0)
                condition_value = max(condition_value, 70.0)  # Минимум 70%
            elif condition_type == "speed_improvement" and avg_response_ms:
                # Порог: среднее время * 0.95 (на 5% быстрее)
                condition_value = avg_response_ms * 0.95
            else:
                condition_type = "accuracy"
                condition_value = 70.0

        # Создание испытания
        challenge = DailyChallenge(
            user_id=user_id,
            date=today,
            questions=questions,
            condition_type=condition_type,
            condition_value=condition_value,
            completed=False,
        )

        session.add(challenge)
        await session.commit()
        await session.refresh(challenge)

        return challenge

    @staticmethod
    async def evaluate_challenge(
        session: AsyncSession,
        drill_session_id: int,
        challenge_id: int
    ) -> dict:
        """
        Оценить результат выполнения испытания.

        Args:
            session: DB сессия
            drill_session_id: ID завершённой DrillSession
            challenge_id: ID DailyChallenge

        Returns:
            Словарь с результатами оценки
        """
        challenge = await session.get(DailyChallenge, challenge_id)
        if not challenge:
            raise ValueError(f"DailyChallenge {challenge_id} not found")

        if challenge.completed:
            return {"success": False, "message": "Challenge already completed"}

        drill_session = await session.get(DrillSession, drill_session_id)
        if not drill_session:
            raise ValueError(f"DrillSession {drill_session_id} not found")

        # Получаем ответы из drill-сессии
        # Предполагаем, что в DrillSession есть информация об ответах
        # В реальной реализации нужно будет получить ответы из связанной таблицы

        # Вычисление результата на основе типа условия
        score = 0.0
        condition_met = False

        if challenge.condition_type == "accuracy":
            # Точность = (правильные ответы / всего ответов) * 100
            total_questions = len(challenge.questions)
            correct_answers = drill_session.correct_answers if hasattr(drill_session, 'correct_answers') else 0
            score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            condition_met = score >= challenge.condition_value

        elif challenge.condition_type == "speed_improvement":
            # Средняя скорость ответа
            if drill_session.avg_response_ms:
                score = drill_session.avg_response_ms
                condition_met = score <= challenge.condition_value
            else:
                score = 0
                condition_met = False

        # Обновление испытания
        challenge.completed = True
        challenge.score = score
        challenge.completed_at = datetime.now(timezone.utc)

        # Начисление очков в WeeklyChallengeEntry
        points_earned = 0
        if condition_met:
            points_earned = 10  # Базовые очки за выполнение

            # Проверка на перевыполнение на 20%+
            if challenge.condition_type == "accuracy":
                if score >= challenge.condition_value * 1.2:
                    points_earned += 5  # Бонус за перевыполнение
            elif challenge.condition_type == "speed_improvement":
                if score <= challenge.condition_value * 0.8:
                    points_earned += 5  # Бонус за значительное улучшение

        # Обновление или создание записи за неделю
        week_start = DailyChallengeService._get_week_start(date.today())

        stmt = select(WeeklyChallengeEntry).where(
            WeeklyChallengeEntry.user_id == challenge.user_id,
            WeeklyChallengeEntry.week_start == week_start
        )
        result = await session.execute(stmt)
        weekly_entry = result.scalar_one_or_none()

        if not weekly_entry:
            weekly_entry = WeeklyChallengeEntry(
                user_id=challenge.user_id,
                week_start=week_start,
                total_points=0,
                challenges_completed=0,
            )
            session.add(weekly_entry)
            await session.flush()

        weekly_entry.total_points += points_earned
        weekly_entry.challenges_completed += 1

        await session.commit()

        return {
            "success": True,
            "condition_met": condition_met,
            "score": score,
            "points_earned": points_earned,
            "condition_type": challenge.condition_type,
            "condition_value": challenge.condition_value,
        }

    @staticmethod
    async def get_today_challenge(session: AsyncSession, user_id: int) -> DailyChallenge | None:
        """
        Получить сегодняшнее испытание пользователя.

        Args:
            session: DB сессия
            user_id: ID пользователя

        Returns:
            DailyChallenge или None если нет испытания
        """
        today = date.today()

        stmt = select(DailyChallenge).where(
            DailyChallenge.user_id == user_id,
            DailyChallenge.date == today
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _get_week_start(d: date) -> date:
        """
        Получить дату начала недели (понедельник) для данной даты.

        Args:
            d: Дата

        Returns:
            Дата понедельника текущей недели
        """
        # weekday() возвращает 0 для понедельника, 6 для воскресенья
        days_since_monday = d.weekday()
        from datetime import timedelta
        return d - timedelta(days=days_since_monday)
