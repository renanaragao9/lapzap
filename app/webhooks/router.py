import logging
from secrets import compare_digest
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["WhatsApp webhook"])


@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_whatsapp_webhook(
    hub_mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    hub_verify_token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    hub_challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
) -> PlainTextResponse:
    is_valid = (
        hub_mode == "subscribe"
        and hub_verify_token is not None
        and compare_digest(hub_verify_token, settings.meta_verify_token)
        and hub_challenge is not None
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verification failed.",
        )

    return PlainTextResponse(hub_challenge)


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def receive_whatsapp_event(event: dict[str, Any]) -> Response:
    logger.info("WhatsApp webhook event received: %s", event)
    return Response(status_code=status.HTTP_200_OK)
