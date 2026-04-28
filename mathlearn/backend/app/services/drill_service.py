"""Сервис для Drill-режима (тренировка таблицы умножения)."""

import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.drill_session import DrillSession
from app.models.sr_card import SRCard
from app.services.mode_config import get_mode_config


@dataclass
class Question:
    """Вопрос для drill-сессии."""
    question_id: int
    factor_a: int
    factor_b: int
    correct_answer: int


@dataclass
class DrillSessionState:
    """Состояние активной drill-сессии."""
    session_id: int
    questions: list[Question] = field(default_factory=list)
    current_index: int = 0
    correct_count: int = 0
    total_answered: int = 0
    response_times_ms: list[int] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None


# Хранилище активных сессий в памяти (для простоты)
# В продакшене лучше использовать Redis
_active_sessions: dict[int, DrillSessionState] = {}


async def _get_weak_tables_for_user(db: AsyncSession, user_id: int, threshold: float = 1.5) -> List[int]:
    """
    Получить список таблиц, где у пользователя есть карточки с ease_factor ниже порога.
    
    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.
        threshold: Порог ease_factor (по умолчанию 1.5).
    
    Returns:
        Список таблиц (factor_b) с проблемными карточками.
    """
    result = await db.execute(
        select(SRCard.factor_b)
        .where(SRCard.user_id == user_id)
        .where(SRCard.ease_factor < threshold)
        .distinct()
    )
    return [row[0] for row in result.all()]


async def _get_unlocked_tables_for_user(db: AsyncSession, user_id: int) -> List[int]:
    """
    Получить список разблокированных таблиц для режима classic.
    
    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.
    
    Returns:
        Список разблокированных таблиц (factor_b).
    """
    result = await db.execute(
        select(SRCard.factor_b)
        .where(SRCard.user_id == user_id)
        .where(SRCard.locked == False)
        .distinct()
    )
    return [row[0] for row in result.all()]


async def start_session(
    db: AsyncSession,
    user_id: int,
    tables: list[int],
    limit: int,
    time_limit_sec: Optional[int] = None,
    mode: str = "classic",
) -> tuple[DrillSession, Question]:
    """
    Начать новую drill-сессию.

    Args:
        db: Сессия базы данных.
        user_id: ID пользователя.
        tables: Список таблиц умножения для тренировки (например, [2, 3, 4]).
        limit: Количество вопросов в сессии.
        time_limit_sec: Ограничение по времени в секундах (опционально).
        mode: Режим обучения (classic, sprinter, weak_spots, streak_hunter, fighter, zen).

    Returns:
        Кортеж (DrillSession, первый вопрос).
    """
    # Получение конфигурации режима
    mode_config = get_mode_config(mode)
    
    # Фильтрация таблиц согласно режиму обучения
    filtered_tables = tables
    
    if mode == "weak_spots":
        # Для режима weak_spots выбираем только таблицы с карточками, где ease_factor < 1.5
        weak_tables = await _get_weak_tables_for_user(db, user_id, threshold=1.5)
        if weak_tables:
            # Пересекаем запрошенные таблицы с проблемными
            filtered_tables = [t for t in tables if t in weak_tables]
            # Если после фильтрации не осталось таблиц, берём все проблемные
            if not filtered_tables:
                filtered_tables = weak_tables[:len(tables)]
    
    elif mode == "classic":
        # Для режима classic — только разблокированные таблицы
        unlocked_tables = await _get_unlocked_tables_for_user(db, user_id)
        filtered_tables = [t for t in tables if t in unlocked_tables]
        # Если все таблицы заблокированы, разрешаем хотя бы первую доступную
        if not filtered_tables and unlocked_tables:
            filtered_tables = unlocked_tables[:1]
    
    elif mode == "fighter":
        # Для режима Fighter применяем ограничение по времени
        if time_limit_sec is None:
            time_limit_sec = mode_config.get("time_limit_sec", 60)
    
    # Генерация пула вопросов из отфильтрованных таблиц
    question_pool = []
    for a in filtered_tables:
        for b in range(1, 11):
            question_pool.append(Question(
                question_id=len(question_pool),
                factor_a=a,
                factor_b=b,
                correct_answer=a * b,
            ))
    
    # Случайный выбор limit вопросов из пула
    if len(question_pool) > limit:
        selected_questions = random.sample(question_pool, limit)
    else:
        selected_questions = question_pool

    # Перемешиваем вопросы
    random.shuffle(selected_questions)

    # Создание записи сессии в БД
    session = DrillSession(
        user_id=user_id,
        total_questions=limit,
        correct_answers=0,
        avg_response_ms=0,
        mode=mode,
        time_limit_sec=time_limit_sec,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Сохранение состояния сессии в памяти
    state = DrillSessionState(
        session_id=session.id,
        questions=selected_questions,
        current_index=0,
        correct_count=0,
        total_answered=0,
        response_times_ms=[],
        started_at=session.started_at,
    )
    _active_sessions[session.id] = state

    # Возврат первого вопроса
    first_question = selected_questions[0] if selected_questions else None

    return session, first_question


async def submit_answer(
    db: AsyncSession,
    session_id: int,
    answer: int,
    response_time_ms: int = 0,
) -> tuple[bool, int, Optional[Question], int]:
    """
    Отправить ответ на вопрос в drill-сессии.

    Args:
        db: Сессия базы данных.
        session_id: ID сессии.
        answer: Ответ пользователя.
        response_time_ms: Время ответа в миллисекундах.

    Returns:
        Кортеж (correct, correct_answer, next_question, score):
            - correct: True если ответ верный.
            - correct_answer: Правильный ответ.
            - next_question: Следующий вопрос или None если сессия завершена.
            - score: Текущий счёт (количество правильных ответов).
    """
    # Получение состояния сессии
    state = _active_sessions.get(session_id)
    if state is None:
        # Сессия не найдена или уже завершена
        raise ValueError(f"Сессия {session_id} не найдена")

    # Проверка, есть ли ещё вопросы
    if state.current_index >= len(state.questions):
        # Сессия завершена
        raise ValueError("Все вопросы в сессии отвечены")

    # Получение текущего вопроса
    current_question = state.questions[state.current_index]

    # Проверка ответа
    correct = answer == current_question.correct_answer

    # Обновление статистики
    state.total_answered += 1
    state.response_times_ms.append(response_time_ms)
    if correct:
        state.correct_count += 1

    # Переход к следующему вопросу
    state.current_index += 1

    # Определение следующего вопроса
    next_question = None
    if state.current_index < len(state.questions):
        next_question = state.questions[state.current_index]
    else:
        # Сессия завершена
        state.ended_at = datetime.now()
        await _finalize_session(db, state)

    return correct, current_question.correct_answer, next_question, state.correct_count


async def _finalize_session(db: AsyncSession, state: DrillSessionState) -> None:
    """
    Завершить сессию и обновить запись в БД.

    Args:
        db: Сессия базы данных.
        state: Состояние сессии.
    """
    # Обновление записи сессии в БД
    result = await db.execute(
        select(DrillSession).where(DrillSession.id == state.session_id)
    )
    session = result.scalar_one_or_none()

    if session is not None:
        session.ended_at = state.ended_at
        session.total_questions = state.total_answered
        session.correct_answers = state.correct_count

        # Вычисление среднего времени ответа
        if state.response_times_ms:
            session.avg_response_ms = round(sum(state.response_times_ms) / len(state.response_times_ms))

        await db.commit()

    # Удаление состояния из памяти
    _active_sessions.pop(state.session_id, None)


async def get_results(session_id: int, db: AsyncSession) -> dict:
    """
    Получить результаты завершённой сессии.

    Args:
        session_id: ID сессии.
        db: Сессия базы данных.

    Returns:
        Словарь с результатами сессии.
    """
    # Загрузка сессии из БД
    result = await db.execute(
        select(DrillSession).where(DrillSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise ValueError(f"Сессия {session_id} не найдена")

    if session.ended_at is None:
        # Сессия ещё активна, получаем данные из памяти
        state = _active_sessions.get(session_id)
        if state:
            accuracy = (state.correct_count / state.total_answered * 100) if state.total_answered > 0 else 0.0
            return {
                "session_id": session.id,
                "total_questions": state.total_answered,
                "correct_answers": state.correct_count,
                "accuracy": accuracy,
                "avg_response_ms": round(sum(state.response_times_ms) / len(state.response_times_ms)) if state.response_times_ms else 0,
                "started_at": session.started_at,
                "ended_at": None,
            }

    # Вычисление точности
    accuracy = (session.correct_answers / session.total_questions * 100) if session.total_questions > 0 else 0.0

    return {
        "session_id": session.id,
        "total_questions": session.total_questions,
        "correct_answers": session.correct_answers,
        "accuracy": accuracy,
        "avg_response_ms": session.avg_response_ms,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
    }


def get_current_question(session_id: int) -> Optional[Question]:
    """
    Получить текущий вопрос активной сессии.

    Args:
        session_id: ID сессии.

    Returns:
        Текущий вопрос или None.
    """
    state = _active_sessions.get(session_id)
    if state is None or state.current_index >= len(state.questions):
        return None
    return state.questions[state.current_index]
