"""SR-движок: реализация алгоритма SM-2 для интервального повторения."""

from datetime import datetime, timedelta
from typing import Protocol


class SRCardLike(Protocol):
    """Протокол для объекта карточки с необходимыми атрибутами."""
    ease_factor: float
    interval_days: int
    repetitions: int


def calculate_next_review(
    card: SRCardLike,
    rating: int,
) -> tuple[float, int, datetime, int]:
    """
    Рассчитать следующие параметры повторения по алгоритму SM-2.

    Args:
        card: Объект карточки с полями ease_factor, interval_days, repetitions.
        rating: Оценка пользователя (1..4), где:
            1 — Не знал
            2 — Трудно
            3 — Знал
            4 — Легко

    Returns:
        Кортеж (ease_factor_new, interval_days_new, next_review_at, repetitions_new):
            - ease_factor_new: новый коэффициент лёгкости (минимум 1.3)
            - interval_days_new: следующий интервал в днях
            - next_review_at: дата следующего повторения
            - repetitions_new: новое количество повторений
    """
    q = rating  # оценка качества ответа (1..4)

    # Формула обновления ease_factor из оригинального SM-2
    # EF_new = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    # В ТЗ используется (4 - q), адаптируем под нашу шкалу 1..4
    ease_factor_new = card.ease_factor + (0.1 - (4 - q) * (0.08 + (4 - q) * 0.02))

    # Ease factor не может быть меньше 1.3
    ease_factor_new = max(1.3, ease_factor_new)

    # Расчёт интервала и количества повторений
    if q < 2:
        # При плохом ответе (1 или 2) сбрасываем повторения и интервал
        interval_days_new = 1
        repetitions_new = 0
    elif card.repetitions == 0:
        # Первое успешное повторение
        interval_days_new = 1
        repetitions_new = 1
    elif card.repetitions == 1:
        # Второе успешное повторение
        interval_days_new = 3
        repetitions_new = 2
    else:
        # Третье и последующие: интервал = предыдущий * ease_factor
        interval_days_new = round(card.interval_days * ease_factor_new)
        repetitions_new = card.repetitions + 1

    # Дата следующего повторения
    next_review_at = datetime.now() + timedelta(days=interval_days_new)

    return ease_factor_new, interval_days_new, next_review_at, repetitions_new
