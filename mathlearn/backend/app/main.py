from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения."""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"message": "Welcome to MathLearn API"}
