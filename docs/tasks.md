# MathLearn — Декомпозиция задач для разработки

**Проект:** MathLearn  
**Версия ТЗ:** 1.0  
**Формат задач:** поэтапная реализация для ИИ-агента  

---

## Правила выполнения задач

- Выполнять задачи строго по этапам, не переходить к следующему без завершения текущего
- Каждая задача — атомарная единица работы с понятным результатом
- Все файлы создавать по структуре проекта из ТЗ
- После каждого этапа должен работать `docker-compose up`

---

## ЭТАП 1 — Инфраструктура

### T-101 Инициализация репозитория
- Создать структуру директорий `mathlearn/backend`, `mathlearn/frontend`
- Добавить `.gitignore` для Python и Node
- Добавить `README.md` с кратким описанием проекта

### T-102 Backend: настройка pyproject.toml
- Настроить `pyproject.toml` с `uv`
- Добавить зависимости: `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, `redis`, `bcrypt`, `pyjwt`
- Настроить `ruff` как линтер и форматер
- Добавить `pytest`, `httpx`, `pytest-asyncio` в dev-зависимости

### T-103 Frontend: инициализация Vite + React + TypeScript
- Создать проект: `npm create vite@latest`
- Установить зависимости: `tailwindcss`, `shadcn-ui`, `zustand`, `axios`, `@tanstack/react-query`, `react-router-dom`
- Настроить `tailwind.config.ts`
- Настроить `vite.config.ts` с proxy `/api` → `http://backend:8000`

### T-104 Docker Compose
- Создать `docker-compose.yml` со следующими сервисами:
  - `postgres:16` — порт 5432, volume `pgdata`
  - `redis:7` — порт 6379
  - `backend` — собирается из `./backend/Dockerfile`, порт 8000
  - `frontend` — собирается из `./frontend/Dockerfile`, порт 5173
- Создать `Dockerfile` для backend (python:3.12-slim)
- Создать `Dockerfile` для frontend (node:20-alpine)
- Создать `.env.example` с переменными:
  - `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`
  - `OLLAMA_URL`, `OLLAMA_MODEL`

**Проверка:** `docker-compose up --build` запускает все 4 сервиса без ошибок

---

## ЭТАП 2 — Backend Foundation

### T-201 Конфигурация приложения
- Создать `app/core/config.py` с `pydantic-settings`
- Параметры: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `OLLAMA_URL`, `OLLAMA_MODEL`
- Создать `app/core/database.py` — async engine и сессии SQLAlchemy
- Создать `app/main.py` — точка входа FastAPI

### T-202 Модели SQLAlchemy
Создать файлы в `app/models/`:
- `user.py` — модель `User` (id, name, email, password_hash, xp, level, current_streak, max_streak, created_at, last_active_at)
- `sr_card.py` — модель `SRCard` (id, user_id, factor_a, factor_b, ease_factor, interval_days, next_review_at, repetitions, lapses)
- `sr_review.py` — модель `SRReview` (id, card_id, user_id, rating, response_time_ms, reviewed_at)
- `drill_session.py` — модель `DrillSession` (id, user_id, started_at, ended_at, total_questions, correct_answers, avg_response_ms)
- `ai_recommendation.py` — модель `AIRecommendation` (id, user_id, lesson_plan JSONB, reasoning, model_name, generated_at)

### T-203 Миграции Alembic
- Инициализировать Alembic: `alembic init alembic`
- Настроить `alembic/env.py` с async engine
- Создать первую миграцию по всем моделям
- Применить миграции

### T-204 Авторизация JWT
Создать `app/core/security.py`:
- Функции `hash_password(password)`, `verify_password(password, hash)`
- Функции `create_access_token(data)`, `create_refresh_token(data)`
- Функцию `decode_token(token)`
- Dependency `get_current_user(token)`

### T-205 Pydantic-схемы
Создать файлы в `app/schemas/`:
- `auth.py` — `RegisterRequest`, `LoginRequest`, `TokenResponse`
- `user.py` — `UserResponse`, `UserUpdateRequest`
- `sr.py` — `SRCardResponse`, `SRReviewRequest`, `SRProgressResponse`
- `drill.py` — `DrillStartRequest`, `DrillAnswerRequest`, `DrillResultResponse`
- `stats.py` — `HeatmapResponse`, `SpeedResponse`, `StreakResponse`
- `ai.py` — `AIRecommendationResponse`, `AIStatusResponse`

### T-206 Auth API
Создать `app/api/auth.py` с роутами:
- `POST /api/auth/register` — хешировать пароль, создать пользователя, создать 100 SR-карточек, вернуть токены
- `POST /api/auth/login` — проверить пароль, вернуть токены
- `POST /api/auth/refresh` — обновить access_token через refresh_token
- `POST /api/auth/logout` — инвалидировать refresh_token в Redis

**Проверка:** `pytest tests/test_auth.py` проходит зелёным

---

## ЭТАП 3 — SR-движок (ядро)

### T-301 SM-2 алгоритм
Создать `app/services/sr_engine.py`:
```
Реализовать функцию calculate_next_review(card, rating) -> (ease_factor, interval_days, next_review_at, repetitions):
  q = rating (1..4)
  ease_factor_new = card.ease_factor + (0.1 - (4 - q) * (0.08 + (4 - q) * 0.02))
  ease_factor_new = max(1.3, ease_factor_new)
  if q < 2: interval = 1, repetitions = 0
  elif repetitions == 0: interval = 1
  elif repetitions == 1: interval = 3
  else: interval = round(prev_interval * ease_factor)
  next_review_at = now + timedelta(days=interval)
```

### T-302 SR API
Создать `app/api/sr.py`:
- `GET /api/sr/queue` — вернуть карточки, где `next_review_at <= now()`, сортировать по `ease_factor ASC`
- `POST /api/sr/review` — принять `{card_id, rating, response_time_ms}`, вызвать SM-2, обновить карточку, сохранить отзыв
- `GET /api/sr/progress` — вернуть матрицу 10×10 с состоянием каждой карточки
- `GET /api/sr/today` — вернуть `{due_count, completed_today}`

### T-303 Unit-тесты SM-2
Создать `tests/test_sr_engine.py`:
- Тест: rating=4 должен увеличивать ease_factor
- Тест: rating=1 должен сбрасывать interval до 1
- Тест: ease_factor не должен падать ниже 1.3
- Тест: третье повторение должно считаться по формуле

**Проверка:** `pytest tests/test_sr_engine.py -v` — все тесты зелёные

---

## ЭТАП 4 — Drill-режим

### T-401 Drill-сервис
Создать `app/services/drill_service.py`:
- `start_session(user_id, tables, limit)` — создать `DrillSession`, сгенерировать список вопросов
- `submit_answer(session_id, answer)` — проверить ответ, записать результат, вернуть следующий вопрос
- `get_results(session_id)` — вернуть итоги сессии

### T-402 Drill API
Создать `app/api/drill.py`:
- `POST /api/drill/start` — принять `{tables, limit, time_limit_sec}`, вернуть `{session_id, first_question}`
- `POST /api/drill/answer` — принять `{session_id, answer}`, вернуть `{correct, correct_answer, next_question, score}`
- `GET /api/drill/results/:session_id` — вернуть итоги

---

## ЭТАП 5 — Геймификация

### T-501 Сервис геймификации
Создать `app/services/gamification.py`:
- `award_xp(user_id, action)` — начислить XP за действие
- `update_streak(user_id)` — обновить streak при завершении ежедневной очереди
- `check_achievements(user_id)` — проверить и разблокировать ачивки
- `get_level(xp)` — вычислить уровень: `level = int((xp / 100) ** (1 / 1.5)) + 1`

### T-502 Статистика API
Создать `app/api/stats.py`:
- `GET /api/stats/heatmap` — матрица 10×10 с `{error_count, avg_time_ms, accuracy}`
- `GET /api/stats/speed?days=30` — динамика скорости ответов по дням
- `GET /api/stats/streak` — текущий и максимальный streak
- `GET /api/stats/achievements` — список достижений с флагом `unlocked`

### T-503 Cron job для streak
- Добавить `APScheduler` в `app/core/scheduler.py`
- Ежедневно в 23:59 проверять, выполнил ли ученик очередь
- Если нет — обнулить streak

---

## ЭТАП 6 — Frontend MVP

### T-601 Настройка роутинга и стора
- Настроить React Router: маршруты `/`, `/learn`, `/drill`, `/table`, `/stats`, `/ai-tutor`, `/profile`
- Создать Zustand store `useAuthStore.ts` с состоянием `user`, `token`, `setUser`, `logout`
- Настроить Axios instance с базовым URL и JWT interceptor

### T-602 Авторизация (UI)
- Страница `LoginPage` — форма email + пароль
- Страница `RegisterPage` — имя, email, пароль
- Редирект на `/` после успешного входа
- Хранить `access_token` в localStorage

### T-603 Компонент FlashCard
Создать `components/FlashCard/`:
- Состояния: `question`, `answer`
- Анимация переворота через CSS `transform: rotateY(180deg)`
- Лицо: `{factor_a} × {factor_b} = ?`
- Обратная сторона: правильный ответ крупным шрифтом

### T-604 Компонент SRRatingButtons
Создать `components/SRRatingButtons/`:
- 4 кнопки: Не знал (1), Трудно (2), Знал (3), Легко (4)
- Цвета: красный, жёлтый, зелёный, синий
- Callback `onRate(rating)` → POST /api/sr/review

### T-605 Страница /learn
Создать `pages/LearnPage.tsx`:
- Хук `useSRQueue` — загружает очередь карточек
- Показывает текущую карточку через `<FlashCard />`
- После ответа показывает `<SRRatingButtons />`
- Прогресс-бар: выполнено / всего в очереди
- Сообщение "Отлично, на сегодня всё!" при пустой очереди

### T-606 Компонент TimerDrill
Создать `components/TimerDrill/`:
- Input с автофокусом для ввода ответа
- Таймер обратного отсчёта (10 секунд)
- Визуальный прогресс-бар таймера
- При истечении — автоматический submit неправильного ответа

### T-607 Страница /drill
Создать `pages/DrillPage.tsx`:
- Форма выбора: какие таблицы, лимит вопросов
- Режим вопросов через `<TimerDrill />`
- Результаты по окончании: точность, скорость, топ ошибок

### T-608 Компонент PythagoreanTable
Создать `components/PythagoreanTable/`:
- SVG или CSS Grid таблица 10×10
- Цвет ячейки по `ease_factor`:
  - красный < 1.5, жёлтый 1.5–2.0, зелёный 2.0–2.5, синий > 2.5
- Tooltip при наведении: `{a} × {b} = {result}`, статистика
- Страница `/table` с этим компонентом и легендой цветов

### T-609 Страница /stats
Создать `pages/StatsPage.tsx`:
- Streak widget — текущий и максимальный
- Heatmap ошибок
- Line chart динамики точности за 30 дней (Recharts)
- Сетка разблокированных ачивок

### T-610 Главная страница
Создать `pages/HomePage.tsx`:
- Streak counter с 🔥 анимацией
- Карточка "Повторить сегодня" — кол-во карточек в очереди
- Мини-таблица прогресса по освоению (% green)
- Блок с рекомендацией от ИИ (если есть)

---

## ЭТАП 7 — AI Tutor (будущее расширение)

### T-701 Подключение Ollama
- Добавить сервис `ollama` в `docker-compose.yml`
- Создать `app/services/ai_tutor.py` с клиентом Ollama
- Добавить env-переменные `OLLAMA_URL` и `OLLAMA_MODEL` в конфиг

### T-702 Сбор контекста ученика
Реализовать метод `collect_student_context(user_id)`:
- Средняя точность за 7 и 30 дней из `sr_reviews`
- Топ-5 карточек с наименьшим `ease_factor`
- Топ-5 карточек с наибольшим `avg(response_time_ms)`
- Прогресс освоения по каждой таблице (% карточек с EF > 2.0)
- Текущий streak и регулярность

### T-703 Генерация lesson plan
Реализовать метод `generate_lesson_plan(user_id)`:
- Формировать prompt из шаблона с подстановкой контекста
- Отправлять запрос в Ollama с форматом `json`
- Парсить ответ в Pydantic-схему
- При ошибке парсинга сохранять fallback-план
- Сохранять результат в `ai_recommendations`

### T-704 Nightly batch job
- Добавить APScheduler job на 00:00
- Запускать `generate_lesson_plan` для всех пользователей с занятием за последние 7 дней
- Логировать результаты

### T-705 AI API эндпоинты
- `GET /api/ai/recommendation` — последний сохранённый план ученика
- `POST /api/ai/generate` — ручной запуск генерации
- `GET /api/ai/status` — статус Ollama и название модели

### T-706 Страница /ai-tutor (UI)
Создать `pages/AITutorPage.tsx`:
- Отображать план на 3 дня
- Карточка каждого дня: фокус-факты, режим, объяснение, кнопка старта
- Индикатор когда был сгенерирован план
- Кнопка "Обновить план" → POST /api/ai/generate
- Сообщение о том, что ИИ работает локально

---

## Зависимости между этапами

```text
ЭТАП 1 (инфраструктура)
  └── ЭТАП 2 (backend foundation)
        ├── ЭТАП 3 (SR-движок)
        │     └── ЭТАП 5 (геймификация)
        └── ЭТАП 4 (drill)
              └── ЭТАП 5 (геймификация)
                    └── ЭТАП 6 (frontend)
                          └── ЭТАП 7 (AI Tutor)
```

---

*Документ для передачи ИИ-агенту. Каждую задачу выполнять по одной, начиная с T-101.*
