# MathLearn — ТЗ: Сценарии обучения (Learning Modes)

**Проект:** MathLearn  
**Документ:** Техническое задание на реализацию функционала выбора сценария обучения  
**Версия:** 1.0  
**Дата:** 28.04.2026  
**Зависит от:** Этапы 1–7 основного ТЗ (T-101 … T-706)

---

## 1. Обзор

Функционал позволяет ученику выбрать один из шести сценариев обучения, каждый из которых меняет поведение SM-2-очереди, Drill-режима, геймификации и AI Tutor. Сценарий задаётся при регистрации (экран онбординга) и может быть изменён в профиле в любой момент.

Реализация затрагивает три слоя: модели данных, бизнес-логику бэкенда и UI фронтенда.

---

## 2. Сценарии и их правила

### 2.1 Классик (`classic`)

**Описание:** последовательное прохождение таблиц от ×2 до ×10. Следующая таблица открывается только после освоения текущей.

**Правила:**
- SR-карточки разделены на группы по `factor_b` (от 2 до 10).
- Карточки группы N+1 имеют флаг `locked=True` пока средний `ease_factor` группы N не достигает `≥ 2.0`.
- Drill доступен только по разблокированным таблицам.
- AI Tutor генерирует линейный план: «Освоить ×3, затем ×4».

**Метрика прогресса:** `% освоенных таблиц` (групп с avg EF ≥ 2.0).

---

### 2.2 Спринтер (`sprinter`)

**Описание:** акцент на скорость ответа. Все таблицы доступны сразу, таймер Drill сокращён до 5 секунд.

**Правила:**
- SR-очередь ограничена 15 карточками в день.
- `DrillStartRequest` создаётся с `time_limit_sec=5`.
- Ачивки завязаны на скорость: «Ответил быстрее 2 сек 10 раз подряд» и т.д.
- На главной странице основной виджет — `avg_response_ms` за последние 7 дней (линейный график).
- AI Tutor в промпте получает инструкцию: `focus=speed`, акцент на часто повторяющихся медленных карточках.

**Метрика прогресса:** средняя скорость ответа (мс), динамика её снижения.

---

### 2.3 Слабые места (`weak_spots`)

**Описание:** очередь формируется только из карточек с наименьшим `ease_factor`. Pythagorean Table — главный экран.

**Правила:**
- `GET /api/sr/queue` при `mode=weak_spots` возвращает 15 карточек с наименьшим `ease_factor`, независимо от `next_review_at`.
- Pythagorean Table (`/table`) устанавливается как домашняя страница по умолчанию.
- AI Tutor: `focus=weak_spots`, топ-5 карточек по `ease_factor ASC` передаются в контекст промпта как приоритет.
- Drill стартует автоматически по проблемным таблицам (тем, где ≥3 карточки с EF < 1.5).

**Метрика прогресса:** количество «красных» ячеек (EF < 1.5) на таблице.

---

### 2.4 Стрик-охотник (`streak_hunter`)

**Описание:** короткие ежедневные сессии. Приоритет — не пропускать ни одного дня.

**Правила:**
- Ежедневная сессия = 5 SR-карточек + 5 вопросов Drill (итого ~3 минуты).
- `DrillStartRequest` с `limit=5`.
- На главной странице — большой анимированный счётчик серии (🔥).
- Push-уведомление / напоминание в 20:00 если сессия не выполнена (реализуется через APScheduler).
- Streak Freeze выдаётся автоматически за каждые 7 дней подряд.
- Бонусный XP: `+50%` за серию ≥ 7 дней, `+100%` за серию ≥ 30 дней.

**Метрика прогресса:** длина текущей серии / максимальная серия.

---

### 2.5 Боец (`fighter`)

**Описание:** соревновательный режим. Ежедневный автоматический вызов, еженедельный лидерборд.

**Правила:**
- Каждый день в 00:00 APScheduler генерирует `DailyChallenge` для пользователя: набор из 20 вопросов с условием победы (например, «точность > 90%» или «быстрее своего вчерашнего результата»).
- После выполнения вызова результат записывается в `WeeklyChallengeEntry`.
- `GET /api/leaderboard?period=week` возвращает топ-10 по сумме очков за неделю среди игроков того же уровня (`±3 уровня`).
- Drill — основной режим, SR — вспомогательный (выполняется после Drill).
- **Pro-фича:** асинхронная дуэль — два игрока проходят одинаковый набор вопросов независимо, результаты сравниваются.

**Метрика прогресса:** место в еженедельном рейтинге / очки за неделю.

---

### 2.6 Дзен (`zen`)

**Описание:** обучение без давления. Нет таймера, нет ачивок за скорость, есть подсказки.

**Правила:**
- Drill запускается без таймера (`time_limit_sec=null`).
- Первые 3 повторения каждой карточки показывают подсказку: `6×7 = 6×6 + 6 = 42`. Поле `hints_remaining` убывает при каждом успешном `review`.
- Ачивки — только за точность и серии, не за скорость.
- XP начисляется за факт завершения сессии, независимо от скорости ответов.
- AI Tutor: `focus=accuracy`, мягкие рекомендации без срочности.

**Метрика прогресса:** средняя точность ответов за 30 дней.

---

## 3. Изменения в модели данных

### 3.1 Модель `User` — добавить поля

```python
# app/models/user.py

learning_mode: str = "classic"  
# Допустимые значения: classic | sprinter | weak_spots | streak_hunter | fighter | zen

xp_multiplier: float = 1.0        # Для streak_hunter и XP Boost
streak_freeze_count: int = 0       # Количество доступных Streak Freeze
```

### 3.2 Модель `SRCard` — добавить поля

```python
# app/models/sr_card.py

locked: bool = False          # Для режима classic: карточка заблокирована
hints_remaining: int = 3      # Для режима zen: подсказки
```

### 3.3 Новая модель `DailyChallenge`

```python
# app/models/daily_challenge.py

class DailyChallenge(Base):
    id: int
    user_id: int                    # FK → users.id
    date: date
    questions: JSON                 # Список вопросов [{factor_a, factor_b}]
    condition_type: str             # accuracy | speed_improvement | streak
    condition_value: float          # Пороговое значение условия победы
    completed: bool = False
    score: float | None             # Результат: достигнутая точность / скорость
    completed_at: datetime | None
```

### 3.4 Новая модель `WeeklyChallengeEntry`

```python
# app/models/weekly_challenge.py

class WeeklyChallengeEntry(Base):
    id: int
    user_id: int                    # FK → users.id
    week_start: date
    total_points: int = 0
    challenges_completed: int = 0
    rank: int | None                # Обновляется раз в час cron-задачей
```

---

## 4. Миграции Alembic

### T-LM-01 Миграция схемы

- Добавить в таблицу `users`: `learning_mode VARCHAR(20) DEFAULT 'classic'`, `xp_multiplier FLOAT DEFAULT 1.0`, `streak_freeze_count INT DEFAULT 0`
- Добавить в таблицу `sr_cards`: `locked BOOLEAN DEFAULT FALSE`, `hints_remaining INT DEFAULT 3`
- Создать таблицы `daily_challenges`, `weekly_challenge_entries`
- Создать индексы: `idx_daily_challenges_user_date`, `idx_weekly_entries_user_week`

---

## 5. Изменения в бэкенде

### 5.1 Сервис конфигурации режимов

**Создать `app/services/mode_config.py`:**

```python
MODE_CONFIG = {
    "classic": {
        "sr_limit": 20,
        "drill_time_limit_sec": 10,
        "unlock_required": True,
        "ai_focus": "sequential",
    },
    "sprinter": {
        "sr_limit": 15,
        "drill_time_limit_sec": 5,
        "unlock_required": False,
        "ai_focus": "speed",
    },
    "weak_spots": {
        "sr_limit": 15,
        "drill_time_limit_sec": 10,
        "unlock_required": False,
        "sr_sort": "ease_factor ASC",
        "ignore_next_review_at": True,
        "ai_focus": "weak_spots",
    },
    "streak_hunter": {
        "sr_limit": 5,
        "drill_time_limit_sec": 10,
        "drill_limit": 5,
        "unlock_required": False,
        "ai_focus": "consistency",
    },
    "fighter": {
        "sr_limit": 10,
        "drill_time_limit_sec": 10,
        "unlock_required": False,
        "daily_challenge": True,
        "leaderboard": True,
        "ai_focus": "competitive",
    },
    "zen": {
        "sr_limit": 20,
        "drill_time_limit_sec": None,
        "unlock_required": False,
        "hints_enabled": True,
        "ai_focus": "accuracy",
    },
}
```

---

### 5.2 Изменения в `sr_engine.py`

**T-LM-02** Модифицировать `GET /api/sr/queue`:

- Читать `user.learning_mode` из БД
- Применять `MODE_CONFIG[mode]` к запросу:
  - `classic` и `sprinter` и остальные: фильтр `next_review_at <= now()`, сортировка по `ease_factor ASC`
  - `weak_spots`: убрать фильтр по `next_review_at`, сортировка `ease_factor ASC NULLS LAST`, лимит 15
  - В режиме `classic`: добавить фильтр `locked = FALSE`
- Возвращать дополнительное поле `hint` в карточке если `zen` и `hints_remaining > 0`

**T-LM-03** Добавить endpoint `POST /api/sr/unlock-check`:

- Вызывается после каждого `review` в режиме `classic`
- Считает `avg(ease_factor)` для текущей группы `factor_b`
- Если `avg >= 2.0` — устанавливает `locked=False` для карточек следующей группы
- Возвращает `{unlocked: bool, next_table: int | null}`

---

### 5.3 Изменения в `drill_service.py`

**T-LM-04** Модифицировать `start_session()`:

- Читать `MODE_CONFIG[user.learning_mode]`
- Применять `time_limit_sec` из конфига (для `zen` передавать `null`)
- В режиме `weak_spots` — генерировать вопросы только из таблиц с карточками где `ease_factor < 1.5`
- В режиме `classic` — генерировать только по разблокированным `factor_b`

---

### 5.4 Изменения в `gamification.py`

**T-LM-05** Модифицировать `award_xp()`:

- Умножать начисленный XP на `user.xp_multiplier`
- Для `streak_hunter`: начислять `+50% XP` если `current_streak >= 7`, `+100%` если `>= 30`
- Для `zen`: не учитывать `response_time_ms` при расчёте бонусного XP
- Для `sprinter`: добавить ачивки за скоростные рекорды (константы в `AchievementType`)

**T-LM-06** Модифицировать `update_streak()` для `streak_hunter`:

- Если у пользователя `streak_freeze_count > 0` и сессия не выполнена — списать один Freeze вместо сброса серии
- Логировать использование Freeze в новую таблицу `streak_freeze_log`

---

### 5.5 Изменения в `ai_tutor.py`

**T-LM-07** Модифицировать `collect_student_context()`:

- Добавить в контекст поле `learning_mode` и `ai_focus` из `MODE_CONFIG`

**T-LM-08** Модифицировать шаблон промпта в `generate_lesson_plan()`:

```
Режим обучения ученика: {learning_mode} (фокус: {ai_focus}).
{"Приоритет — последовательное освоение таблиц." if ai_focus == "sequential"}
{"Приоритет — минимизация времени ответа. Делай упор на быстрые факты." if ai_focus == "speed"}
{"Приоритет — слабые карточки. Топ проблем: {weak_cards}." if ai_focus == "weak_spots"}
{"Приоритет — регулярность. Каждый день, коротко." if ai_focus == "consistency"}
{"Приоритет — подготовка к соревнованиям. Акцент на смешанных таблицах." if ai_focus == "competitive"}
{"Приоритет — точность без спешки. Не упоминай скорость." if ai_focus == "accuracy"}
```

---

### 5.6 Новый сервис `DailyChallengeService`

**Создать `app/services/daily_challenge.py`** (для режима `fighter`):

**T-LM-09** Метод `generate_challenge(user_id)`:
- Генерировать 20 вопросов случайным образом по всем таблицам
- Определять тип условия:
  - `accuracy` — если у пользователя уже есть результаты, ставить порог `avg_accuracy + 5%`
  - `speed_improvement` — порог `avg_response_ms * 0.95`
  - Первая сессия — всегда `accuracy >= 70%`
- Сохранять в `DailyChallenge`

**T-LM-10** Метод `evaluate_challenge(session_id, challenge_id)`:
- После завершения DrillSession сравнивать результат с условием
- Начислять очки в `WeeklyChallengeEntry`: 10 очков за выполнение, `+5` бонус если перевыполнено на 20%+
- Обновлять `DailyChallenge.completed = True`

---

### 5.7 Новые API-эндпоинты

**Создать `app/api/modes.py`:**

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/modes` | Список всех сценариев с описаниями |
| `POST` | `/api/modes/select` | Установить сценарий пользователю `{mode: string}` |
| `GET` | `/api/modes/current` | Текущий сценарий и его параметры |

**Добавить в `app/api/drill.py`:**

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/challenge/today` | Текущий DailyChallenge пользователя |
| `POST` | `/api/challenge/start` | Запустить DrillSession из DailyChallenge |

**Добавить в `app/api/stats.py`:**

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/leaderboard` | Лидерборд `?period=week`, `?level_range=3` |

---

### 5.8 Новые Pydantic-схемы

**Добавить в `app/schemas/`:**

```python
# modes.py
class ModeInfo(BaseModel):
    mode: str
    title: str
    description: str
    icon: str
    is_pro: bool
    primary_metric: str

class ModeSelectRequest(BaseModel):
    mode: Literal["classic", "sprinter", "weak_spots", "streak_hunter", "fighter", "zen"]

class ModeSelectResponse(BaseModel):
    mode: str
    applied: bool

# challenge.py
class DailyChallengeResponse(BaseModel):
    id: int
    date: date
    questions_count: int
    condition_type: str
    condition_value: float
    completed: bool
    score: float | None

# leaderboard.py
class LeaderboardEntry(BaseModel):
    rank: int
    user_name: str
    total_points: int
    challenges_completed: int
    is_current_user: bool

class LeaderboardResponse(BaseModel):
    period: str
    entries: list[LeaderboardEntry]
    current_user_rank: int | None
```

---

### 5.9 APScheduler — новые задачи

**Добавить в `app/core/scheduler.py`:**

**T-LM-11** Задача `generate_daily_challenges` (00:05 каждый день):
- Выбрать всех активных пользователей с `learning_mode = "fighter"`
- Для каждого вызвать `DailyChallengeService.generate_challenge(user_id)`

**T-LM-12** Задача `recalculate_leaderboard` (каждый час):
- Пересчитать `rank` в `WeeklyChallengeEntry` для текущей недели
- Группировать по `level ± 3` (использовать `get_level(xp)` из `gamification.py`)

**T-LM-13** Задача `send_streak_reminders` (20:00 каждый день):
- Выбрать пользователей с `learning_mode = "streak_hunter"` у которых `last_active_at < today`
- Добавить запись в `notifications` (реализовать минимальную таблицу `notifications` или логировать в Redis)

---

## 6. Изменения во фронтенде

### 6.1 Онбординг-экран выбора сценария

**T-LM-14** Создать `pages/OnboardingModePage.tsx`:
- Показывается один раз после регистрации (если `user.learning_mode == null` или при первом входе)
- 6 карточек с иконкой, названием, описанием, бейджем `PRO` для `fighter`
- Кнопка `«Начать»` → `POST /api/modes/select` → redirect `/`
- Карточки: горизонтальный скролл на мобильном, сетка 2×3 на десктопе

---

### 6.2 Компонент `ModeCard`

**T-LM-15** Создать `components/ModeCard/index.tsx`:

```typescript
interface ModeCardProps {
  mode: ModeInfo;
  selected: boolean;
  onSelect: (mode: string) => void;
}
```

- Состояния: `default`, `selected` (подсвечена рамкой), `pro-locked` (если `is_pro && !user.isPro`)
- Анимация выбора: лёгкий scale-up + смена цвета рамки
- Бейдж `PRO` в правом верхнем углу для платных режимов

---

### 6.3 Адаптация `HomePage.tsx`

**T-LM-16** Рендерить виджеты в зависимости от `user.learning_mode`:

| Режим | Главный виджет | Второстепенный виджет |
|-------|---------------|----------------------|
| `classic` | Прогресс по таблицам (% групп ≥ 2.0) | Карточки в очереди сегодня |
| `sprinter` | График avg_response_ms за 7 дней | Карточки в очереди |
| `weak_spots` | Мини-таблица 10×10 с красными ячейками | Топ-3 слабые карточки |
| `streak_hunter` | 🔥 Большой streak-счётчик | Прогресс мини-сессии (5/5) |
| `fighter` | DailyChallenge (условие, кнопка старта) | Место в лидерборде |
| `zen` | Точность за 30 дней | Карточки с подсказками |

---

### 6.4 Адаптация `LearnPage.tsx`

**T-LM-17** Изменения в `useSRQueue`:
- Передавать `mode` в запрос `GET /api/sr/queue?mode=...`
- В режиме `zen`: показывать подсказку под вопросом если `hints_remaining > 0`
- В режиме `classic`: показывать прогресс-бар разблокировки следующей таблицы

---

### 6.5 Адаптация `DrillPage.tsx`

**T-LM-18**:
- В режиме `streak_hunter`: автоматически запускать сессию из 5 вопросов без экрана настройки
- В режиме `fighter`: добавить кнопку `«Принять вызов дня»` поверх стандартного Drill
- В режиме `zen`: скрыть таймер-прогрессбар, показывать только вопрос и input

---

### 6.6 Новая страница `/leaderboard`

**T-LM-19** Создать `pages/LeaderboardPage.tsx` (только для `fighter`):
- Таблица топ-10 с аватарами, именами, очками, бейджами
- Текущий пользователь выделен другим фоном
- Переключатель: `Эта неделя` / `Прошлая неделя`
- Если пользователь не `fighter` — заглушка с описанием режима и кнопкой переключения

---

### 6.7 Страница `/profile` — секция смены режима

**T-LM-20** Добавить в `ProfilePage.tsx` секцию `«Сценарий обучения»`:
- Показывает текущий режим с иконкой и описанием
- Кнопка `«Изменить»` → открывает модальное окно с `<ModeCard />` для каждого режима
- При смене режима показывать предупреждение: `«Некоторые настройки сессии будут сброшены»`

---

## 7. Unit-тесты

### T-LM-21 `tests/test_mode_sr_queue.py`

- Тест: в режиме `classic` возвращаются только `locked=False` карточки
- Тест: в режиме `weak_spots` игнорируется `next_review_at`, сортировка по `ease_factor ASC`
- Тест: в режиме `streak_hunter` лимит очереди = 5
- Тест: `POST /api/sr/unlock-check` разблокирует следующую группу при avg EF ≥ 2.0
- Тест: `POST /api/sr/unlock-check` не разблокирует при avg EF < 2.0

### T-LM-22 `tests/test_gamification_modes.py`

- Тест: `award_xp` умножает XP на `xp_multiplier`
- Тест: `streak_hunter` с серией ≥ 7 применяет `+50% XP`
- Тест: `update_streak` в `streak_hunter` списывает Freeze вместо обнуления серии
- Тест: `update_streak` в `streak_hunter` обнуляет серию если `streak_freeze_count = 0`

### T-LM-23 `tests/test_daily_challenge.py`

- Тест: `generate_challenge` создаёт ровно 20 вопросов
- Тест: условие `speed_improvement` устанавливает порог `avg_ms * 0.95`
- Тест: `evaluate_challenge` начисляет очки при выполнении условия
- Тест: `evaluate_challenge` не начисляет очки при невыполнении условия

---

## 8. Этапы реализации и зависимости

```
T-LM-01  Миграция схемы БД
    └── T-LM-02  SR queue с учётом режима
    └── T-LM-03  Unlock-check endpoint (classic)
    └── T-LM-04  Drill mode config
    └── T-LM-05  Gamification XP multiplier
    └── T-LM-06  Streak Freeze logic
    └── T-LM-07  AI context + mode
    └── T-LM-08  AI prompt template
    └── T-LM-09  DailyChallenge generate
          └── T-LM-10  DailyChallenge evaluate
          └── T-LM-11  APScheduler: generate challenges
          └── T-LM-12  APScheduler: leaderboard recalc
    └── T-LM-13  APScheduler: streak reminders
          └── T-LM-14  Onboarding UI
          └── T-LM-15  ModeCard component
          └── T-LM-16  HomePage adaption
          └── T-LM-17  LearnPage adaption
          └── T-LM-18  DrillPage adaption
          └── T-LM-19  LeaderboardPage
          └── T-LM-20  ProfilePage mode switch
T-LM-21..23  Unit-тесты (параллельно с реализацией)
```

---

## 9. Монетизация и доступность режимов

| Режим | Free | Pro |
|-------|------|-----|
| Классик | ✅ | ✅ |
| Дзен | ✅ | ✅ |
| Спринтер | ✅ | ✅ |
| Слабые места | ✅ | ✅ |
| Стрик-охотник | ⚠️ Лимит: 3 Freeze/мес | Безлимит Freeze |
| Боец | 🔒 Только просмотр лидерборда | ✅ Полный доступ + дуэли |

Поле `is_pro` проверяется в `GET /api/modes` и на фронтенде в `<ModeCard />`.

---

## 10. Переменные окружения — дополнения

Добавить в `.env.example`:

```env
# Learning modes
DEFAULT_LEARNING_MODE=classic
LEADERBOARD_LEVEL_RANGE=3          # ±N уровней для группировки лидерборда
STREAK_REMINDER_HOUR=20            # Час отправки напоминания (UTC)
DAILY_CHALLENGE_QUESTIONS=20       # Кол-во вопросов в daily challenge
```

---

*Документ для передачи ИИ-агенту. Выполнять задачи строго по зависимостям, начиная с T-LM-01.*
