# MathLearn

Веб-приложение для изучения таблицы умножения детьми 7–10 лет с использованием интервального повторения (алгоритм SM-2) и AI-тьютора.

## 🎯 Цель

Помочь детям выучить таблицу умножения через:
- Интервальное повторение (SM-2)
- Тренажёр (drill mode)
- Геймификацию (уровни, достижения, стрики)
- Персональные рекомендации от локального AI (Ollama)

## 🛠️ Стек

**Backend:**
- Python 3.12 + FastAPI
- SQLAlchemy (async) + PostgreSQL 16
- Redis 7 (кеширование, сессии)
- Alembic (миграции)
- JWT (авторизация)

**Frontend:**
- React 18 + TypeScript
- Vite
- Tailwind CSS + shadcn-ui
- Zustand (state management)
- React Query

**Инфраструктура:**
- Docker Compose
- Ollama (локальный AI)

## 📁 Структура проекта

```
mathlearn/
├── backend/          # FastAPI приложение
├── frontend/         # React приложение
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 🚀 Быстрый старт

```bash
# Клонировать репозиторий
git clone <repo-url>
cd mathlearn

# Скопировать переменные окружения
cp .env.example .env

# Запустить все сервисы
docker-compose up --build
```

Приложение будет доступно:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📋 Этапы разработки

1. ✅ Инфраструктура (T-101 — T-104)
2. ⏳ Backend Foundation (T-201 — T-206)
3. ⏳ SR-движок (T-301 — T-303)
4. ⏳ Drill Mode (T-401 — T-402)
5. ⏳ Геймификация (T-501 — T-503)
6. ⏳ Frontend (T-601 — T-607)
7. ⏳ AI Tutor (T-701 — T-706)

## 📄 Документация

- [Техническое задание](docs/mathlearn_tz.md)
- [Промпт для ИИ-агента](docs/prompt.md)
- [Декомпозиция задач](docs/tasks.md)