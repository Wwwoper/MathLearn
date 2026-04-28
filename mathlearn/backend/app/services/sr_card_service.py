"""Сервис для работы с SR-карточками и поддержки режимов обучения."""

from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.sr_card import SRCard
from app.models.user import User
from app.services.mode_config import get_mode_config


class SRCardService:
    """Сервис для управления SR-карточками с поддержкой режимов обучения."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_due_cards(
        self,
        user: User,
        limit: Optional[int] = None,
    ) -> List[SRCard]:
        """
        Получить карточки для повторения с учётом режима обучения.

        Args:
            user: Пользователь.
            limit: Максимальное количество карточек (если не указано, берётся из конфига режима).

        Returns:
            Список карточек для повторения.
        """
        mode = user.learning_mode
        config = get_mode_config(mode)

        # Определение лимита
        if limit is None:
            limit = config.get("sr_limit", 20)

        now = datetime.now()

        # Построение базового запроса
        query = select(SRCard).where(SRCard.user_id == user.id)

        # Применение фильтра locked для режима classic
        if config.get("unlock_required", False):
            query = query.where(SRCard.locked == False)

        # Применение фильтра по времени и сортировки в зависимости от режима
        if mode == "weak_spots":
            # Режим "Слабые места": игнорируем next_review_at, сортируем по ease_factor ASC
            query = query.order_by(SRCard.ease_factor.asc())
        else:
            # Остальные режимы: фильтр по next_review_at <= now
            query = query.where(SRCard.next_review_at <= now)
            # Сортировка по ease_factor ASC (сначала самые лёгкие для забывания)
            query = query.order_by(SRCard.ease_factor.asc())

        # Применение лимита
        query = query.limit(limit)

        result = await self.db.execute(query)
        cards = result.scalars().all()

        return list(cards)

    async def get_card_by_id(self, card_id: int, user_id: int) -> Optional[SRCard]:
        """
        Получить карточку по ID с проверкой принадлежности пользователю.

        Args:
            card_id: ID карточки.
            user_id: ID пользователя.

        Returns:
            Карточка или None.
        """
        result = await self.db.execute(
            select(SRCard)
            .where(SRCard.id == card_id)
            .where(SRCard.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def unlock_next_table(
        self,
        user: User,
        current_table: int,
    ) -> Tuple[bool, Optional[int]]:
        """
        Проверить и разблокировать следующую таблицу в режиме classic.

        Args:
            user: Пользователь.
            current_table: Текущая таблица (factor_b).

        Returns:
            Кортеж (unlocked: bool, next_table: int | None):
                - unlocked: True если следующая таблица была разблокирована.
                - next_table: ID следующей таблицы или None.
        """
        # Проверка среднего ease_factor для текущей группы
        result = await self.db.execute(
            select(func.avg(SRCard.ease_factor))
            .where(SRCard.user_id == user.id)
            .where(SRCard.factor_b == current_table)
        )
        avg_ef = result.scalar() or 0.0

        if avg_ef >= 2.0:
            # Разблокировка следующей таблицы
            next_table = current_table + 1
            if next_table <= 10:
                await self.db.execute(
                    update(SRCard)
                    .where(SRCard.user_id == user.id)
                    .where(SRCard.factor_b == next_table)
                    .values(locked=False)
                )
                await self.db.commit()
                return True, next_table

        return False, None

    async def decrement_hint(self, card: SRCard, mode: str = "classic") -> int:
        """
        Уменьшить количество подсказок для карточки.
        В режиме Zen подсказки бесконечные и не расходуются.

        Args:
            card: Карточка.
            mode: Режим обучения.

        Returns:
            Оставшееся количество подсказок.
        """
        # В режиме Zen подсказки бесконечные
        if mode == "zen":
            return card.hints_remaining
        
        if card.hints_remaining > 0:
            card.hints_remaining -= 1
            await self.db.commit()
        return card.hints_remaining

    async def get_weak_tables(self, user_id: int, threshold: float = 1.5) -> List[int]:
        """
        Получить список таблиц с карточками, имеющими ease_factor ниже порога.

        Args:
            user_id: ID пользователя.
            threshold: Порог ease_factor.

        Returns:
            Список таблиц (factor_b) с проблемными карточками.
        """
        result = await self.db.execute(
            select(SRCard.factor_b)
            .where(SRCard.user_id == user_id)
            .where(SRCard.ease_factor < threshold)
            .group_by(SRCard.factor_b)
            .having(func.count(SRCard.id) >= 3)
        )
        return [row[0] for row in result.all()]

    async def get_unlocked_tables(self, user_id: int) -> List[int]:
        """
        Получить список разблокированных таблиц для режима classic.

        Args:
            user_id: ID пользователя.

        Returns:
            Список разблокированных таблиц (factor_b).
        """
        result = await self.db.execute(
            select(SRCard.factor_b)
            .where(SRCard.user_id == user_id)
            .where(SRCard.locked == False)
            .distinct()
        )
        return [row[0] for row in result.all()]

    async def get_all_user_cards(self, user_id: int) -> List[SRCard]:
        """
        Получить все карточки пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            Список всех карточек пользователя.
        """
        result = await self.db.execute(
            select(SRCard)
            .where(SRCard.user_id == user_id)
            .order_by(SRCard.factor_a, SRCard.factor_b)
        )
        return list(result.scalars().all())


# Импортируем update здесь, чтобы избежать циклического импорта
from sqlalchemy import update
