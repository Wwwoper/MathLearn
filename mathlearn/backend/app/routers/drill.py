"""Роуты для Drill-режима (тренировка таблицы умножения)."""

import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.drill import (
    DrillStartRequest,
    DrillAnswerRequest,
    DrillResultResponse,
    DrillQuestionResponse,
    DrillAnswerResponse,
)
from app.services import drill_service

router = APIRouter(prefix="/drill", tags=["Drill-режим"])


@router.post("/start")
async def start_drill_session(
    request: DrillStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Начать новую drill-сессию.

    Принимает {tables, limit, time_limit_sec}, возвращает {session_id, first_question}.
    """
    try:
        session, first_question = await drill_service.start_session(
            db=db,
            user_id=current_user.id,
            tables=request.tables,
            limit=request.limit,
            time_limit_sec=request.time_limit_sec,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании сессии: {str(e)}",
        )

    question_response = DrillQuestionResponse(
        question_id=first_question.question_id,
        factor_a=first_question.factor_a,
        factor_b=first_question.factor_b,
        session_id=session.id,
    )

    return {
        "session_id": session.id,
        "first_question": question_response,
    }


@router.post("/answer")
async def submit_drill_answer(
    request: DrillAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Отправить ответ на вопрос в drill-сессии.

    Принимает {session_id, answer}, возвращает {correct, correct_answer, next_question, score}.
    """
    # Получаем время ответа (в реальном приложении передавалось бы от клиента)
    response_time_ms = 0  # Заглушка, в реальности должно приходить от клиента

    try:
        correct, correct_answer, next_question, score = await drill_service.submit_answer(
            db=db,
            session_id=request.session_id,
            answer=request.answer,
            response_time_ms=response_time_ms,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке ответа: {str(e)}",
        )

    next_question_response = None
    if next_question:
        next_question_response = DrillQuestionResponse(
            question_id=next_question.question_id,
            factor_a=next_question.factor_a,
            factor_b=next_question.factor_b,
            session_id=request.session_id,
        )

    return DrillAnswerResponse(
        correct=correct,
        correct_answer=correct_answer,
        next_question=next_question_response,
        score=score,
    )


@router.get("/results/{session_id}", response_model=DrillResultResponse)
async def get_drill_results(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Получить итоги завершённой drill-сессии.
    """
    try:
        results = await drill_service.get_results(session_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении результатов: {str(e)}",
        )

    # Проверка принадлежности сессии пользователю
    if results["session_id"] != session_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён",
        )

    return DrillResultResponse(**results)
