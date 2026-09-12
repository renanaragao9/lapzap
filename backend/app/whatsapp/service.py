import asyncio
import logging
import random
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models.message_log import MessageLog
from app.numbers.service import get_active_phone_number, is_rate_limited
from app.whatsapp.schemas import BroadcastResult, EvolutionWebhookPayload

logger = logging.getLogger(__name__)


class WhatsAppService:
    async def send_text(self, number: str, text: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.evolution_api_url}/message/sendText/"
                f"{settings.evolution_instance_name}",
                headers={"apikey": settings.evolution_api_key},
                json={"number": number, "text": text},
            )
            response.raise_for_status()
            return response.json()

    async def broadcast(
        self,
        numbers: list[str],
        text: str,
        session: AsyncSession,
        delay_seconds: float = 2.0,
    ) -> list[BroadcastResult]:
        results: list[BroadcastResult] = []

        for number in numbers:
            try:
                data = await self.send_text(number, text)
                message_id = data.get("key", {}).get("id") or str(uuid4())
                session.add(
                    MessageLog(
                        external_message_id=message_id,
                        message_type="TEXT",
                        direction="OUTBOUND",
                        payload=data,
                        processed=True,
                        blocked=False,
                    )
                )
                results.append(BroadcastResult(number=number, status="sent"))
            except Exception as exc:  # - reporta erro por número, segue o lote
                logger.exception("Broadcast send failed: number=%s", number)
                results.append(
                    BroadcastResult(number=number, status="error", detail=str(exc))
                )

            await asyncio.sleep(delay_seconds + random.uniform(0, 1))

        await session.commit()
        return results

    async def process_webhook(
        self,
        payload: EvolutionWebhookPayload,
        raw_payload: dict[str, Any],
        session: AsyncSession,
    ) -> None:
        logger.info("Evolution webhook payload received: %s", raw_payload)

        if not self.is_message_event(payload):
            logger.info("Evolution webhook event ignored: event=%s", payload.event)
            return

        data = payload.data or {}
        raw_key = data.get("key")
        key: dict[str, Any] = raw_key if isinstance(raw_key, dict) else {}
        raw_message = data.get("message")
        message: dict[str, Any] = raw_message if isinstance(raw_message, dict) else {}
        remote_jid = key.get("remoteJid") or key.get("remoteJidAlt")
        sender = remote_jid.split("@", 1)[0] if isinstance(remote_jid, str) else None
        message_type = data.get("messageType") or self.get_message_type(message)
        message_id = key.get("id") or data.get("id")

        logger.info(
            "Evolution message event: instance=%s sender=%s type=%s text=%s message_id=%s",
            payload.instance or data.get("instance"),
            sender,
            message_type,
            self.get_text(message),
            message_id,
        )

        if sender is None or not isinstance(message_id, str):
            return

        phone_number = await get_active_phone_number(f"+{sender}", session)
        authorized = phone_number is not None
        rate_limited = (
            await is_rate_limited(phone_number.id, session) if phone_number else False
        )
        blocked = not authorized or rate_limited

        session.add(
            MessageLog(
                phone_number_id=phone_number.id if phone_number else None,
                external_message_id=message_id,
                message_type=message_type or "UNKNOWN",
                direction="INBOUND",
                payload=raw_payload,
                processed=False,
                blocked=blocked,
            )
        )
        await session.commit()

        logger.info(
            "Evolution sender authorization: sender=%s authorized=%s rate_limited=%s blocked=%s",
            sender,
            authorized,
            rate_limited,
            blocked,
        )

    @staticmethod
    def is_message_event(payload: EvolutionWebhookPayload) -> bool:
        event = payload.event or ""
        return "message" in event.lower() and isinstance(payload.data, dict)

    @staticmethod
    def get_message_type(message: dict[str, Any]) -> str | None:
        if "conversation" in message or "extendedTextMessage" in message:
            return "TEXT"
        if "imageMessage" in message:
            return "IMAGE"
        return None

    @staticmethod
    def get_text(message: dict[str, Any]) -> str | None:
        conversation = message.get("conversation")
        if isinstance(conversation, str):
            return conversation

        extended_text = message.get("extendedTextMessage")
        if isinstance(extended_text, dict):
            text = extended_text.get("text")
            if isinstance(text, str):
                return text

        return None
