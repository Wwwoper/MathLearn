"""Тесты сервиса геймификации."""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.gamification import get_level, award_xp, update_streak, check_achievements, get_user_stats


class TestGetLevel:
    """Тесты функции вычисления уровня."""

    def test_level_at_zero_xp(self):
        """Уровень 1 при 0 XP."""
        assert get_level(0) == 1

    def test_level_at_100_xp(self):
        """Уровень 2 при 100 XP."""
        assert get_level(100) == 2

    def test_level_at_500_xp(self):
        """Проверка уровня при 500 XP."""
        level = get_level(500)
        assert level > 1

    def test_level_increases_with_xp(self):
        """Уровень растёт с увеличением XP."""
        assert get_level(0) < get_level(100) < get_level(500) < get_level(1000)

    def test_level_formula_accuracy(self):
        """Проверка точности формулы."""
        # level = int((xp / 100) ** (1 / 1.5)) + 1
        # При xp=0: int(0 ** 0.667) + 1 = 0 + 1 = 1
        assert get_level(0) == 1
        # При xp=100: int(1 ** 0.667) + 1 = 1 + 1 = 2
        assert get_level(100) == 2
        # При xp=800: int(8 ** 0.667) + 1 = int(3.999) + 1 = 4
        assert get_level(800) == 4


class TestAwardXP:
    """Тесты функции начисления XP."""

    @pytest.mark.asyncio
    async def test_award_xp_review_correct(self):
        """Начисление XP за правильный ответ."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.xp = 0
        user.level = 1
        session.get = AsyncMock(return_value=user)

        xp_amount = await award_xp(session, 1, "review_correct")

        assert xp_amount == 10
        assert user.xp == 10
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_award_xp_review_easy(self):
        """Начисление XP за лёгкий ответ."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.xp = 0
        user.level = 1
        session.get = AsyncMock(return_value=user)

        xp_amount = await award_xp(session, 1, "review_easy")

        assert xp_amount == 15
        assert user.xp == 15

    @pytest.mark.asyncio
    async def test_award_xp_drill_complete(self):
        """Начисление XP за завершение drill-сессии."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.xp = 0
        user.level = 1
        session.get = AsyncMock(return_value=user)

        xp_amount = await award_xp(session, 1, "drill_complete")

        assert xp_amount == 50
        assert user.xp == 50

    @pytest.mark.asyncio
    async def test_award_xp_level_up(self):
        """Повышение уровня при достижении порога XP."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.xp = 95  # Почти уровень 2
        user.level = 1
        session.get = AsyncMock(return_value=user)

        # Начисляем 10 XP, должно получиться 105 -> уровень 2
        await award_xp(session, 1, "review_correct")

        assert user.xp == 105
        assert user.level == 2

    @pytest.mark.asyncio
    async def test_award_xp_user_not_found(self):
        """Ошибка при отсутствии пользователя."""
        session = AsyncMock(spec=AsyncSession)
        session.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="User .* not found"):
            await award_xp(session, 999, "review_correct")

    @pytest.mark.asyncio
    async def test_award_xp_default_action(self):
        """Начисление XP за неизвестное действие (по умолчанию 5)."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.xp = 0
        user.level = 1
        session.get = AsyncMock(return_value=user)

        xp_amount = await award_xp(session, 1, "unknown_action")

        assert xp_amount == 5
        assert user.xp == 5


class TestUpdateStreak:
    """Тесты функции обновления streak."""

    @pytest.mark.asyncio
    async def test_update_streak_first_time(self):
        """Первое обновление streak."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.current_streak = 0
        user.max_streak = 0
        user.last_active_at = None
        session.get = AsyncMock(return_value=user)

        streak, updated = await update_streak(session, 1)

        assert streak == 1
        assert updated is True
        assert user.current_streak == 1
        assert user.max_streak == 1

    @pytest.mark.asyncio
    async def test_update_streak_consecutive_day(self):
        """Обновление streak на следующий день."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.current_streak = 5
        user.max_streak = 5
        user.last_active_at = datetime.now(timezone.utc) - timedelta(days=1)
        session.get = AsyncMock(return_value=user)

        streak, updated = await update_streak(session, 1)

        assert streak == 6
        assert updated is True
        assert user.current_streak == 6

    @pytest.mark.asyncio
    async def test_update_streak_same_day(self):
        """Активность в тот же день не меняет streak."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.current_streak = 5
        user.max_streak = 5
        user.last_active_at = datetime.now(timezone.utc)
        session.get = AsyncMock(return_value=user)

        streak, updated = await update_streak(session, 1)

        assert streak == 5
        assert updated is False

    @pytest.mark.asyncio
    async def test_update_streak_after_gap(self):
        """Сброс streak после пропуска дня."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.current_streak = 10
        user.max_streak = 10
        user.last_active_at = datetime.now(timezone.utc) - timedelta(days=3)
        session.get = AsyncMock(return_value=user)

        streak, updated = await update_streak(session, 1)

        assert streak == 1
        assert updated is True
        assert user.current_streak == 1

    @pytest.mark.asyncio
    async def test_update_streak_new_max(self):
        """Обновление max_streak при превышении."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.current_streak = 5
        user.max_streak = 5
        user.last_active_at = datetime.now(timezone.utc) - timedelta(days=1)
        session.get = AsyncMock(return_value=user)

        streak, updated = await update_streak(session, 1)

        assert user.max_streak == 6

    @pytest.mark.asyncio
    async def test_update_streak_user_not_found(self):
        """Ошибка при отсутствии пользователя."""
        session = AsyncMock(spec=AsyncSession)
        session.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="User .* not found"):
            await update_streak(session, 999)


class TestCheckAchievements:
    """Тесты функции проверки ачивок."""

    @pytest.mark.asyncio
    async def test_check_achievements_level_based(self):
        """Ачивки по уровню."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.level = 10
        user.current_streak = 0
        user.max_streak = 0
        session.get = AsyncMock(return_value=user)
        
        # Мок для SRReview query
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        achievements = await check_achievements(session, 1)

        assert "novice" in achievements  # level >= 5
        assert "intermediate" in achievements  # level >= 10
        assert "advanced" not in achievements  # level < 20

    @pytest.mark.asyncio
    async def test_check_achievements_streak_based(self):
        """Ачивки по streak."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.level = 1
        user.current_streak = 7
        user.max_streak = 7
        session.get = AsyncMock(return_value=user)
        
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        achievements = await check_achievements(session, 1)

        assert "week_warrior" in achievements
        assert "month_master" not in achievements

    @pytest.mark.asyncio
    async def test_check_achievements_no_duplicates(self):
        """Отсутствие дубликатов в ачивках."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.level = 100
        user.current_streak = 365
        user.max_streak = 365
        session.get = AsyncMock(return_value=user)
        
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        achievements = await check_achievements(session, 1)

        # Проверяем что нет дубликатов
        assert len(achievements) == len(set(achievements))

    @pytest.mark.asyncio
    async def test_check_achievements_user_not_found(self):
        """Ошибка при отсутствии пользователя."""
        session = AsyncMock(spec=AsyncSession)
        session.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="User .* not found"):
            await check_achievements(session, 999)


class TestGetUserStats:
    """Тесты функции получения статистики пользователя."""

    @pytest.mark.asyncio
    async def test_get_user_stats(self):
        """Получение полной статистики."""
        session = AsyncMock(spec=AsyncSession)
        user = MagicMock()
        user.id = 1
        user.xp = 500
        user.level = 3
        user.current_streak = 5
        user.max_streak = 10
        user.last_active_at = datetime.now(timezone.utc)
        session.get = AsyncMock(return_value=user)
        
        # Мок для check_achievements
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        stats = await get_user_stats(session, 1)

        assert stats["user_id"] == 1
        assert stats["xp"] == 500
        assert stats["level"] == 3
        assert stats["current_streak"] == 5
        assert stats["max_streak"] == 10
        assert "achievements" in stats

    @pytest.mark.asyncio
    async def test_get_user_stats_user_not_found(self):
        """Ошибка при отсутствии пользователя."""
        session = AsyncMock(spec=AsyncSession)
        session.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="User .* not found"):
            await get_user_stats(session, 999)
