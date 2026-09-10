from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.core.config import settings
from app.numbers.router import router as numbers_router
from app.webhooks.router import router as whatsapp_webhook_router

app = FastAPI(title=settings.app_name)
app.include_router(auth_router)
app.include_router(numbers_router)
app.include_router(whatsapp_webhook_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
