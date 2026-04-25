"""Тесты для Drill API."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_async_session
from app.core.deps import get_current_user


# Тестовая база данных в памяти - используем SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Создание тестовой сессии базы данных."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Импортируем модели для создания таблиц
    from app.models.user import User
    
    async with engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(User.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def client(db_session):
    """Фикстура для тестового клиента."""
    async def override_get_async_session():
        yield db_session
    
    app.dependency_overrides[get_async_session] = override_get_async_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """Фикстура для мок-объекта пользователя."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_drill_session():
    """Фикстура для мок-объекта drill-сессии."""
    session = MagicMock()
    session.id = 123
    session.user_id = 1
    session.started_at = datetime.now()
    session.ended_at = None
    session.total_questions = 10
    session.correct_answers = 0
    session.avg_response_ms = 0
    return session


@pytest.fixture
def mock_question():
    """Фикстура для мок-объекта вопроса."""
    question = MagicMock()
    question.question_id = 1
    question.factor_a = 3
    question.factor_b = 4
    question.correct_answer = 12
    return question


class TestDrillStart:
    """Тесты для эндпоинта POST /api/drill/start."""

    @pytest.mark.asyncio
    async def test_start_drill_session_success(self, client, mock_user, mock_drill_session, mock_question):
        """Тест успешного создания drill-сессии."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.start_session", new_callable=AsyncMock) as mock_start:
            mock_start.return_value = (mock_drill_session, mock_question)
            
            response = await client.post(
                "/api/drill/start",
                json={"tables": [2, 3], "limit": 10, "time_limit_sec": 300},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "first_question" in data
            assert data["first_question"]["factor_a"] == 3
            assert data["first_question"]["factor_b"] == 4
            mock_start.assert_called_once()
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_start_drill_session_invalid_tables(self, client, mock_user):
        """Тест создания сессии с пустым списком таблиц."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        response = await client.post(
            "/api/drill/start",
            json={"tables": [], "limit": 10},
        )
        
        assert response.status_code == 422
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_start_drill_session_invalid_limit(self, client, mock_user):
        """Тест создания сессии с недопустимым лимитом."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        response = await client.post(
            "/api/drill/start",
            json={"tables": [2], "limit": 0},
        )
        
        assert response.status_code == 422
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_start_drill_session_service_error(self, client, mock_user):
        """Тест обработки ошибки сервиса при создании сессии."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.start_session", new_callable=AsyncMock) as mock_start:
            mock_start.side_effect = Exception("Database error")
            
            response = await client.post(
                "/api/drill/start",
                json={"tables": [2], "limit": 10},
            )
            
            assert response.status_code == 500
        
        app.dependency_overrides.clear()


class TestDrillAnswer:
    """Тесты для эндпоинта POST /api/drill/answer."""

    @pytest.mark.asyncio
    async def test_submit_answer_correct(self, client, mock_user):
        """Тест правильного ответа."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.submit_answer", new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = (True, 12, None, 1)
            
            response = await client.post(
                "/api/drill/answer",
                json={"session_id": 123, "answer": 12},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["correct"] is True
            assert data["correct_answer"] == 12
            assert data["score"] == 1
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_submit_answer_incorrect(self, client, mock_user):
        """Тест неправильного ответа."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.submit_answer", new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = (False, 12, None, 0)
            
            response = await client.post(
                "/api/drill/answer",
                json={"session_id": 123, "answer": 10},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["correct"] is False
            assert data["correct_answer"] == 12
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_submit_answer_session_not_found(self, client, mock_user):
        """Тест ответа для несуществующей сессии."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.submit_answer", new_callable=AsyncMock) as mock_submit:
            mock_submit.side_effect = ValueError("Сессия не найдена")
            
            response = await client.post(
                "/api/drill/answer",
                json={"session_id": 999, "answer": 12},
            )
            
            assert response.status_code == 404
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_submit_answer_with_next_question(self, client, mock_user, mock_question):
        """Тест ответа с возвратом следующего вопроса."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.submit_answer", new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = (True, 12, mock_question, 2)
            
            response = await client.post(
                "/api/drill/answer",
                json={"session_id": 123, "answer": 12},
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["next_question"] is not None
            assert data["next_question"]["question_id"] == 1
        
        app.dependency_overrides.clear()


class TestDrillResults:
    """Тесты для эндпоинта GET /api/drill/results/{session_id}."""

    @pytest.mark.asyncio
    async def test_get_results_success(self, client, mock_user, mock_drill_session):
        """Тест успешного получения результатов."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.get_results", new_callable=AsyncMock) as mock_results:
            mock_results.return_value = {
                "session_id": 123,
                "total_questions": 10,
                "correct_answers": 8,
                "accuracy": 80.0,
                "avg_response_ms": 1500,
                "started_at": datetime.now(),
                "ended_at": datetime.now(),
            }
            
            response = await client.get("/api/drill/results/123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == 123
            assert data["total_questions"] == 10
            assert data["correct_answers"] == 8
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_results_not_found(self, client, mock_user):
        """Тест получения результатов для несуществующей сессии."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.get_results", new_callable=AsyncMock) as mock_results:
            mock_results.side_effect = ValueError("Сессия не найдена")
            
            response = await client.get("/api/drill/results/999")
            
            assert response.status_code == 404
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_results_forbidden(self, client, mock_user):
        """Тест доступа к чужой сессии."""
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        with patch("app.routers.drill.drill_service.get_results", new_callable=AsyncMock) as mock_results:
            mock_results.return_value = {
                "session_id": 999,
                "total_questions": 10,
                "correct_answers": 8,
                "accuracy": 80.0,
                "avg_response_ms": 1500,
                "started_at": datetime.now(),
                "ended_at": datetime.now(),
            }
            
            response = await client.get("/api/drill/results/123")
            
            assert response.status_code == 403
        
        app.dependency_overrides.clear()
