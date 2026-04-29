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
        rating: Оценка пользователя (1..5), где:
            1 — 😠 Не знал совсем
            2 — 😕 Трудно
            3 — 😐 Знал нормально
            4 — 🙂 Хорошо
            5 — 🤩 Отлично

    Returns:
        Кортеж (ease_factor_new, interval_days_new, next_review_at, repetitions_new):
            - ease_factor_new: новый коэффициент лёгкости (минимум 1.3)
            - interval_days_new: следующий интервал в днях
            - next_review_at: дата следующего повторения
            - repetitions_new: новое количество повторений
    """
    # Преобразуем рейтинг 1-5 в шкалу SM-2 (0-4 для формулы)
    # Для совместимости с оригинальным SM-2 используем q = rating - 1 (0..4)
    q = rating - 1  # теперь 0..4, где 0=плохо, 4=отлично

    # Формула обновления ease_factor из оригинального SM-2
    # EF_new = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    # q теперь в шкале 0..4, что соответствует оригинальному SM-2
    # rating=5 (q=4): delta = +0.00 (EF не меняется)
    # rating=4 (q=3): delta = -0.14 (небольшое уменьшение)
    # rating=3 (q=2): delta = -0.32 (заметное уменьшение)
    # rating=2 (q=1): delta = -0.54 (сильное уменьшение)
    # rating=1 (q=0): delta = -0.80 (очень сильное уменьшение)
    ease_factor_new = card.ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

    # Ease factor не может быть меньше 1.3
    ease_factor_new = max(1.3, ease_factor_new)

    # Расчёт интервала и количества повторений
    if q <= 1:  # rating 1 или 2 (😠 или 😕)
        # При плохом ответе сбрасываем повторения и интервал
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
