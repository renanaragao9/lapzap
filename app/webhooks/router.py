import logging
from secrets import compare_digest
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_session
from app.numbers.service import is_phone_authorized

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["WhatsApp webhook"])

Session = Annotated[AsyncSession, Depends(get_session)]


def extract_sender_phone_numbers(event: dict[str, Any]) -> list[str]:
    phone_numbers: list[str] = []

    for entry in event.get("entry", []):
        for change in entry.get("changes", []):
            for message in change.get("value", {}).get("messages", []):
                sender = message.get("from")
                if isinstance(sender, str) and sender.isdigit():
                    phone_numbers.append(f"+{sender}")

    return phone_numbers


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
async def receive_whatsapp_event(event: dict[str, Any], session: Session) -> Response:
    logger.info("WhatsApp webhook event received: %s", event)

    for phone_number in extract_sender_phone_numbers(event):
        authorized = await is_phone_authorized(phone_number, session)
        logger.info(
            "WhatsApp sender authorization: phone_number=%s authorized=%s",
            phone_number,
            authorized,
        )

    return Response(status_code=status.HTTP_200_OK)
