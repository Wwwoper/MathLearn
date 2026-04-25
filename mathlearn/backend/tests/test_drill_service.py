"""Тесты для Drill-сервиса."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.drill_service import (
    Question,
    DrillSessionState,
    start_session,
    submit_answer,
    get_results,
    get_current_question,
    _active_sessions,
)


@pytest.fixture
def mock_db():
    """Фикстура для мок-объекта базы данных."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Фикстура для мок-объекта пользователя."""
    user = MagicMock()
    user.id = 1
    return user


@pytest.fixture(autouse=True)
def clear_sessions():
    """Очистка активных сессий перед каждым тестом."""
    _active_sessions.clear()
    yield
    _active_sessions.clear()


class TestQuestion:
    """Тесты для класса Question."""

    def test_question_creation(self):
        """Тест создания вопроса."""
        q = Question(question_id=1, factor_a=3, factor_b=4, correct_answer=12)
        assert q.question_id == 1
        assert q.factor_a == 3
        assert q.factor_b == 4
        assert q.correct_answer == 12

    def test_question_calculation(self):
        """Тест правильного вычисления ответа."""
        for a in range(2, 10):
            for b in range(1, 11):
                q = Question(question_id=1, factor_a=a, factor_b=b, correct_answer=a * b)
                assert q.correct_answer == a * b


class TestDrillSessionState:
    """Тесты для класса DrillSessionState."""

    def test_state_initialization(self):
        """Тест инициализации состояния сессии."""
        state = DrillSessionState(session_id=1)
        assert state.session_id == 1
        assert state.questions == []
        assert state.current_index == 0
        assert state.correct_count == 0
        assert state.total_answered == 0
        assert state.response_times_ms == []
        assert state.ended_at is None

    def test_state_with_questions(self):
        """Тест состояния с вопросами."""
        questions = [
            Question(question_id=1, factor_a=2, factor_b=3, correct_answer=6),
            Question(question_id=2, factor_a=4, factor_b=5, correct_answer=20),
        ]
        state = DrillSessionState(session_id=1, questions=questions)
        assert len(state.questions) == 2
        assert state.current_index == 0


class TestStartSession:
    """Тесты для функции start_session."""

    @pytest.mark.asyncio
    async def test_start_session_creates_session(self, mock_db, mock_user):
        """Тест создания новой сессии."""
        # Настройка мока для БД
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.started_at = datetime.now()
        mock_db.add = MagicMock()
        mock_db.refresh = AsyncMock()
        
        # Патчим создание сессии в БД
        with patch('app.services.drill_service.DrillSession') as MockDrillSession:
            MockDrillSession.return_value = mock_session
            
            session, first_question = await start_session(
                db=mock_db,
                user_id=mock_user.id,
                tables=[2, 3],
                limit=5,
            )
            
            assert session.id == 1
            assert first_question is not None
            assert first_question.factor_a in [2, 3]
            assert 1 <= first_question.factor_b <= 10

    @pytest.mark.asyncio
    async def test_start_session_generates_correct_pool(self, mock_db, mock_user):
        """Тест генерации пула вопросов из выбранных таблиц."""
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.started_at = datetime.now()
        
        with patch('app.services.drill_service.DrillSession') as MockDrillSession:
            MockDrillSession.return_value = mock_session
            
            session, first_question = await start_session(
                db=mock_db,
                user_id=mock_user.id,
                tables=[2],  # Только таблица умножения на 2
                limit=5,
            )
            
            # Все вопросы должны быть из таблицы на 2
            assert first_question.factor_a == 2
            assert 1 <= first_question.factor_b <= 10

    @pytest.mark.asyncio
    async def test_start_session_respects_limit(self, mock_db, mock_user):
        """Тест соблюдения лимита вопросов."""
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.started_at = datetime.now()
        
        with patch('app.services.drill_service.DrillSession') as MockDrillSession:
            MockDrillSession.return_value = mock_session
            
            session, first_question = await start_session(
                db=mock_db,
                user_id=mock_user.id,
                tables=[2, 3, 4, 5],  # 4 таблицы = 40 возможных вопросов
                limit=10,  # Но просим только 10
            )
            
            # Проверяем, что сессия создана с правильным лимитом
            assert mock_session.total_questions == 10


class TestSubmitAnswer:
    """Тесты для функции submit_answer."""

    @pytest.mark.asyncio
    async def test_submit_answer_correct(self, mock_db):
        """Тест правильного ответа."""
        # Создаём тестовую сессию
        questions = [
            Question(question_id=1, factor_a=2, factor_b=3, correct_answer=6),
            Question(question_id=2, factor_a=4, factor_b=5, correct_answer=20),
        ]
        state = DrillSessionState(session_id=1, questions=questions)
        _active_sessions[1] = state
        
        correct, correct_answer, next_question, score = await submit_answer(
            db=mock_db,
            session_id=1,
            answer=6,  # Правильный ответ
            response_time_ms=1000,
        )
        
        assert correct is True
        assert correct_answer == 6
        assert score == 1
        assert next_question is not None
        assert next_question.factor_a == 4
        assert next_question.factor_b == 5

    @pytest.mark.asyncio
    async def test_submit_answer_incorrect(self, mock_db):
        """Тест неправильного ответа."""
        questions = [
            Question(question_id=1, factor_a=2, factor_b=3, correct_answer=6),
        ]
        state = DrillSessionState(session_id=1, questions=questions)
        _active_sessions[1] = state
        
        correct, correct_answer, next_question, score = await submit_answer(
            db=mock_db,
            session_id=1,
            answer=5,  # Неправильный ответ
            response_time_ms=1000,
        )
        
        assert correct is False
        assert correct_answer == 6
        assert score == 0
        assert next_question is None  # Вопросы закончились

    @pytest.mark.asyncio
    async def test_submit_answer_session_not_found(self, mock_db):
        """Тест ошибки при несуществующей сессии."""
        with pytest.raises(ValueError, match="Сессия .* не найдена"):
            await submit_answer(
                db=mock_db,
                session_id=999,
                answer=6,
            )

    @pytest.mark.asyncio
    async def test_submit_answer_completes_session(self, mock_db):
        """Тест завершения сессии после последнего вопроса."""
        questions = [
            Question(question_id=1, factor_a=2, factor_b=3, correct_answer=6),
        ]
        state = DrillSessionState(session_id=1, questions=questions)
        _active_sessions[1] = state
        
        # Отвечаем на единственный вопрос
        await submit_answer(
            db=mock_db,
            session_id=1,
            answer=6,
            response_time_ms=1000,
        )
        
        # Сессия должна быть завершена и удалена из памяти
        assert 1 not in _active_sessions


class TestGetResults:
    """Тесты для функции get_results."""

    @pytest.mark.asyncio
    async def test_get_results_active_session(self, mock_db):
        """Тест получения результатов активной сессии."""
        questions = [
            Question(question_id=1, factor_a=2, factor_b=3, correct_answer=6),
            Question(question_id=2, factor_a=4, factor_b=5, correct_answer=20),
        ]
        state = DrillSessionState(session_id=1, questions=questions)
        state.correct_count = 1
        state.total_answered = 1
        state.response_times_ms = [1000]
        _active_sessions[1] = state
        
        # Мок для БД
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.started_at = datetime.now()
        mock_session.ended_at = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result
        
        results = await get_results(session_id=1, db=mock_db)
        
        assert results["session_id"] == 1
        assert results["total_questions"] == 1
        assert results["correct_answers"] == 1
        assert results["accuracy"] == 100.0

    @pytest.mark.asyncio
    async def test_get_results_completed_session(self, mock_db):
        """Тест получения результатов завершённой сессии."""
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.total_questions = 10
        mock_session.correct_answers = 8
        mock_session.avg_response_ms = 1500
        mock_session.started_at = datetime.now()
        mock_session.ended_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result
        
        results = await get_results(session_id=1, db=mock_db)
        
        assert results["session_id"] == 1
        assert results["total_questions"] == 10
        assert results["correct_answers"] == 8
        assert results["accuracy"] == 80.0
        assert results["avg_response_ms"] == 1500

    @pytest.mark.asyncio
    async def test_get_results_not_found(self, mock_db):
        """Тест ошибки при несуществующей сессии."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(ValueError, match="Сессия .* не найдена"):
            await get_results(session_id=999, db=mock_db)


class TestGetCurrentQuestion:
    """Тесты для функции get_current_question."""

    def test_get_current_question_exists(self):
        """Тест получения текущего вопроса."""
        questions = [
            Question(question_id=1, factor_a=2, factor_b=3, correct_answer=6),
            Question(question_id=2, factor_a=4, factor_b=5, correct_answer=20),
        ]
        state = DrillSessionState(session_id=1, questions=questions)
        _active_sessions[1] = state
        
        q = get_current_question(1)
        assert q is not None
        assert q.factor_a == 2
        assert q.factor_b == 3

    def test_get_current_question_no_session(self):
        """Тест отсутствия сессии."""
        q = get_current_question(999)
        assert q is None

    def test_get_current_question_all_answered(self):
        """Тест когда все вопросы отвечены."""
        questions = [
            Question(question_id=1, factor_a=2, factor_b=3, correct_answer=6),
        ]
        state = DrillSessionState(session_id=1, questions=questions)
        state.current_index = 1  # Все вопросы пройдены
        _active_sessions[1] = state
        
        q = get_current_question(1)
        assert q is None
