#!/usr/bin/env python3
"""
Скрипт для создания таблиц в базе данных.
Запускается один раз при первом запуске приложения.
"""

import asyncio
import sys

# Добавляем путь к проекту
sys.path.insert(0, '/app')

from app.core.database import engine, Base
from app.models import user, sr_card, sr_review, drill_session, ai_recommendation  # noqa: F401


async def init_db():
    """Инициализация базы данных: создание всех таблиц."""
    
    try:
        async with engine.begin() as conn:
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
            
            print("✅ Все таблицы успешно созданы!")
            
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
