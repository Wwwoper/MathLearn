from fastapi import FastAPI

from app.core.config import settings
from app.routers import auth_router, sr_router, drill_router
from app.api.stats import router as stats_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Подключение роутов
app.include_router(auth_router)
app.include_router(sr_router, prefix="/api")
app.include_router(drill_router, prefix="/api")
app.include_router(stats_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Welcome to MathLearn API"}
