"""Тесты для авторизации."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import JSON

from app.main import app
from app.core.database import Base, get_async_session
from app.core.config import settings


# Тестовая база данных в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Создание тестовой сессии базы данных."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        # Создаем только таблицы users и sr_cards для тестов auth
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def client(db_session):
    """Создание тестового клиента."""
    async def override_get_async_session():
        yield db_session
    
    app.dependency_overrides[get_async_session] = override_get_async_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user(client, db_session):
    """Тест регистрации пользователя."""
    response = await client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client, db_session):
    """Тест регистрации с дублирующимся email."""
    # Первая регистрация
    await client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    
    # Вторая регистрация с тем же email
    response = await client.post(
        "/api/auth/register",
        json={
            "name": "Another User",
            "email": "test@example.com",
            "password": "password456",
        },
    )
    
    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user(client, db_session):
    """Тест входа пользователя."""
    # Регистрация
    await client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "login@example.com",
            "password": "password123",
        },
    )
    
    # Вход
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, db_session):
    """Тест входа с неправильным паролем."""
    # Регистрация
    await client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "wrong@example.com",
            "password": "password123",
        },
    )
    
    # Вход с неправильным паролем
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "wrongpassword",
        },
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client, db_session):
    """Тест обновления токена."""
    # Регистрация
    register_response = await client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "refresh@example.com",
            "password": "password123",
        },
    )
    
    refresh_token = register_response.json()["refresh_token"]
    
    # Обновление токена
    response = await client.post(
        "/api/auth/refresh",
        params={"refresh_token": refresh_token},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_current_user(client, db_session):
    """Тест получения информации о текущем пользователе."""
    # Регистрация
    register_response = await client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "me@example.com",
            "password": "password123",
        },
    )
    
    access_token = register_response.json()["access_token"]
    
    # Получение информации о пользователе
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["name"] == "Test User"
