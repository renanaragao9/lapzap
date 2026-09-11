from typing import Any

from fastapi import APIRouter

from app.whatsapp.schemas import EvolutionWebhookPayload, WebhookResponse
from app.whatsapp.service import WhatsAppService

router = APIRouter(prefix="/api/v1/webhooks", tags=["Evolution API webhook"])

whatsapp_service = WhatsAppService()


@router.post("/whatsapp", response_model=WebhookResponse)
async def receive_evolution_webhook(event: dict[str, Any]) -> WebhookResponse:
    payload = EvolutionWebhookPayload.model_validate(event)
    whatsapp_service.process_webhook(payload, event)
    return WebhookResponse()
