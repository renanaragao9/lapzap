from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.whatsapp.schemas import EvolutionWebhookPayload, WebhookResponse
from app.whatsapp.service import WhatsAppService

router = APIRouter(prefix="/api/v1/webhooks", tags=["Evolution API webhook"])

whatsapp_service = WhatsAppService()

Session = Annotated[AsyncSession, Depends(get_session)]


@router.post("/whatsapp", response_model=WebhookResponse)
async def receive_evolution_webhook(
    event: dict[str, Any],
    session: Session,
) -> WebhookResponse:
    payload = EvolutionWebhookPayload.model_validate(event)
    await whatsapp_service.process_webhook(payload, event, session)
    return WebhookResponse()
