from fastapi import FastAPI

from app.core.config import settings
from app.routers import auth_router, sr_router, drill_router
from app.api.stats import router as stats_router
from app.core.scheduler import start_scheduler


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Подключение роутов
app.include_router(auth_router, prefix="/api")
app.include_router(sr_router, prefix="/api")
app.include_router(drill_router, prefix="/api")
app.include_router(stats_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Запуск планировщика при старте приложения."""
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Остановка планировщика при завершении работы приложения."""
    from app.core.scheduler import shutdown_scheduler
    shutdown_scheduler()


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Welcome to MathLearn API"}
