from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.business.router import router as businesses_router
from app.business_info.router import router as business_info_router
from app.business_integrations.router import router as business_integrations_router
from app.core.config import settings
from app.messages.router import router as messages_router
from app.numbers.router import router as numbers_router
from app.users.router import router as users_router
from app.whatsapp.router import router as evolution_webhook_router

app = FastAPI(title=settings.app_name)
app.include_router(auth_router)
app.include_router(businesses_router)
app.include_router(business_info_router)
app.include_router(business_integrations_router)
app.include_router(numbers_router)
app.include_router(messages_router)
app.include_router(users_router)
app.include_router(evolution_webhook_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
