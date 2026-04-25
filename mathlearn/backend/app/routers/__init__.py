"""Роуты приложения."""

from app.routers.auth import router as auth_router
from app.routers.sr import router as sr_router

__all__ = ["auth_router", "sr_router"]
