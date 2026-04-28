"""Модели SQLAlchemy для приложения MathLearn."""

from app.core.database import Base
from app.models.user import User
from app.models.sr_card import SRCard
from app.models.sr_review import SRReview
from app.models.drill_session import DrillSession
from app.models.ai_recommendation import AIRecommendation
from app.models.daily_challenge import DailyChallenge
from app.models.weekly_challenge import WeeklyChallengeEntry

__all__ = [
    "Base",
    "User",
    "SRCard",
    "SRReview",
    "DrillSession",
    "AIRecommendation",
    "DailyChallenge",
    "WeeklyChallengeEntry",
]
