import logging
from dataclasses import dataclass
from secrets import compare_digest
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models.message_log import MessageLog
from app.database.session import get_session
from app.numbers.service import get_active_phone_number

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["WhatsApp webhook"])

Session = Annotated[AsyncSession, Depends(get_session)]


@dataclass(frozen=True)
class IncomingMessage:
    phone_number: str
    external_message_id: str
    message_type: str


def extract_incoming_messages(event: dict[str, Any]) -> list[IncomingMessage]:
    messages: list[IncomingMessage] = []

    for entry in event.get("entry", []):
        for change in entry.get("changes", []):
            for message in change.get("value", {}).get("messages", []):
                sender = message.get("from")
                message_id = message.get("id")
                raw_type = message.get("type")
                message_type = (
                    raw_type.upper() if raw_type in {"text", "image"} else "UNKNOWN"
                )

                if (
                    isinstance(sender, str)
                    and sender.isdigit()
                    and isinstance(message_id, str)
                ):
                    messages.append(
                        IncomingMessage(
                            phone_number=f"+{sender}",
                            external_message_id=message_id,
                            message_type=message_type,
                        )
                    )

    return messages


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

    for message in extract_incoming_messages(event):
        phone_number = await get_active_phone_number(message.phone_number, session)
        authorized = phone_number is not None
        session.add(
            MessageLog(
                phone_number_id=phone_number.id if phone_number else None,
                external_message_id=message.external_message_id,
                message_type=message.message_type,
                direction="INBOUND",
                payload=event,
                processed=False,
                blocked=not authorized,
            )
        )
        logger.info(
            "WhatsApp sender authorization: phone_number=%s authorized=%s",
            message.phone_number,
            authorized,
        )

    await session.commit()

    return Response(status_code=status.HTTP_200_OK)
