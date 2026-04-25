"""Роуты приложения."""

from app.routers.auth import router as auth_router
from app.routers.sr import router as sr_router
from app.routers.drill import router as drill_router

__all__ = ["auth_router", "sr_router", "drill_router"]
