"""Pydantic схемы для приложения."""

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    TokenPayload,
)
from app.schemas.user import UserResponse, UserUpdateRequest
from app.schemas.sr import SRCardResponse, SRReviewRequest, SRProgressResponse
from app.schemas.drill import (
    DrillStartRequest,
    DrillAnswerRequest,
    DrillResultResponse,
    DrillQuestionResponse,
    DrillAnswerResponse,
)
from app.schemas.stats import (
    HeatmapResponse,
    SpeedResponse,
    StreakResponse,
    AchievementResponse,
    AchievementsResponse,
)
from app.schemas.ai import AIRecommendationResponse, AIStatusResponse, LessonPlanDay

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "TokenPayload",
    # User
    "UserResponse",
    "UserUpdateRequest",
    # SR
    "SRCardResponse",
    "SRReviewRequest",
    "SRProgressResponse",
    # Drill
    "DrillStartRequest",
    "DrillAnswerRequest",
    "DrillResultResponse",
    "DrillQuestionResponse",
    "DrillAnswerResponse",
    # Stats
    "HeatmapResponse",
    "SpeedResponse",
    "StreakResponse",
    "AchievementResponse",
    "AchievementsResponse",
    # AI
    "AIRecommendationResponse",
    "AIStatusResponse",
    "LessonPlanDay",
]