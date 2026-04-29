"""Тесты для SR-движка (алгоритм SM-2)."""

from datetime import datetime, timedelta
from app.services.sr_engine import calculate_next_review


class MockSRCard:
    """Моковый объект карточки для тестов."""

    def __init__(
        self,
        ease_factor: float = 2.5,
        interval_days: int = 0,
        repetitions: int = 0,
    ):
        self.ease_factor = ease_factor
        self.interval_days = interval_days
        self.repetitions = repetitions


def test_rating_4_increases_ease_factor():
    """Тест: rating=5 должен сохранять ease_factor (максимальная оценка)."""
    card = MockSRCard(ease_factor=2.5, interval_days=1, repetitions=2)
    ef_new, interval, next_review, reps = calculate_next_review(card, rating=5)

    # rating=5 в SM-2 не увеличивает EF выше начального, но и не уменьшает
    assert ef_new >= 2.5, f"ease_factor должен остаться >= 2.5, но получил {ef_new}"
    assert reps == 3, f"repetitions должен быть 3, но получил {reps}"


def test_rating_4_good_performance():
    """Тест: rating=4 должен давать хороший результат (небольшое снижение EF)."""
    card = MockSRCard(ease_factor=2.5, interval_days=1, repetitions=2)
    ef_new, interval, next_review, reps = calculate_next_review(card, rating=4)

    # rating=4 немного снижает EF, но всё равно хорошо
    assert ef_new > 2.0, f"ease_factor должен быть > 2.0, но получил {ef_new}"
    assert reps == 3, f"repetitions должен быть 3, но получил {reps}"


def test_rating_1_resets_interval():
    """Тест: rating=1 должен сбрасывать interval до 1."""
    card = MockSRCard(ease_factor=2.5, interval_days=10, repetitions=5)
    ef_new, interval, next_review, reps = calculate_next_review(card, rating=1)

    assert interval == 1, f"interval должен быть 1, но получил {interval}"
    assert reps == 0, f"repetitions должен быть сброшен в 0, но получил {reps}"


def test_ease_factor_minimum():
    """Тест: ease_factor не должен падать ниже 1.3."""
    card = MockSRCard(ease_factor=1.5, interval_days=5, repetitions=3)
    # Многократные плохие ответы
    for _ in range(10):
        ef_new, _, _, _ = calculate_next_review(card, rating=1)
        card.ease_factor = ef_new

    assert ef_new >= 1.3, f"ease_factor не должен быть меньше 1.3, но получил {ef_new}"
    assert abs(ef_new - 1.3) < 0.001, f"ease_factor должен быть ровно 1.3, но получил {ef_new}"


def test_third_repetition_uses_formula():
    """Тест: третье повторение должно считаться по формуле interval = prev * EF."""
    # После двух успешных повторений: interval=3, repetitions=2
    card = MockSRCard(ease_factor=2.5, interval_days=3, repetitions=2)
    ef_new, interval, next_review, reps = calculate_next_review(card, rating=3)

    # interval = round(3 * 2.5) = 8 (при rating=3 EF почти не меняется)
    expected_interval = round(3 * 2.5)
    assert interval == expected_interval, f"interval должен быть {expected_interval}, но получил {interval}"
    assert reps == 3, f"repetitions должен быть 3, но получил {reps}"


def test_first_repetition():
    """Тест: первое повторение устанавливает interval=1."""
    card = MockSRCard(ease_factor=2.5, interval_days=0, repetitions=0)
    ef_new, interval, next_review, reps = calculate_next_review(card, rating=3)

    assert interval == 1, f"interval должен быть 1, но получил {interval}"
    assert reps == 1, f"repetitions должен быть 1, но получил {reps}"


def test_second_repetition():
    """Тест: второе повторение устанавливает interval=3."""
    card = MockSRCard(ease_factor=2.5, interval_days=1, repetitions=1)
    ef_new, interval, next_review, reps = calculate_next_review(card, rating=3)

    assert interval == 3, f"interval должен быть 3, но получил {interval}"
    assert reps == 2, f"repetitions должен быть 2, но получил {reps}"


def test_rating_2_decreases_ease_factor():
    """Тест: rating=2 должен уменьшать ease_factor."""
    card = MockSRCard(ease_factor=2.5, interval_days=5, repetitions=3)
    ef_new, interval, next_review, reps = calculate_next_review(card, rating=2)

    assert ef_new < 2.5, f"ease_factor должен уменьшиться, но получил {ef_new}"


def test_next_review_date():
    """Тест: next_review_at должна быть через interval дней от текущего времени."""
    card = MockSRCard(ease_factor=2.5, interval_days=5, repetitions=3)
    ef_new, interval, next_review, reps = calculate_next_review(card, rating=4)

    expected_date = datetime.now() + timedelta(days=interval)
    # Разница во времени должна быть менее секунды (из-за времени выполнения)
    diff = abs((next_review - expected_date).total_seconds())
    assert diff < 1, f"next_review_at должна быть через {interval} дней, но разница {diff} сек"
