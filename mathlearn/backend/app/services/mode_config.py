"""
Конфигурация режимов обучения (Learning Modes)
Согласно ТЗ раздел 5.1
"""

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

VALID_MODES = list(MODE_CONFIG.keys())


def get_mode_config(mode: str) -> dict:
    """
    Получить конфигурацию для указанного режима обучения.
    
    Args:
        mode: Название режима (classic, sprinter, weak_spots, streak_hunter, fighter, zen)
    
    Returns:
        dict: Конфигурация режима
    
    Raises:
        ValueError: Если режим не найден
    """
    if mode not in MODE_CONFIG:
        raise ValueError(f"Неверный режим обучения: {mode}. Допустимые значения: {VALID_MODES}")
    return MODE_CONFIG[mode]


def is_mode_valid(mode: str) -> bool:
    """
    Проверить валидность режима обучения.
    
    Args:
        mode: Название режима для проверки
    
    Returns:
        bool: True если режим валиден
    """
    return mode in VALID_MODES
