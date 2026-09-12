import asyncio
import json
import logging
import random
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.service import (
    build_system_prompt,
    get_business_by_instance,
    is_rate_limited,
)
from app.core.config import settings
from app.database.models.message_log import MessageLog
from app.llm.chat_service import ask
from app.numbers.service import get_active_phone_number_for_business
from app.whatsapp.media_storage import save_image
from app.whatsapp.schemas import BroadcastResult, EvolutionWebhookPayload

logger = logging.getLogger(__name__)


def _sanitize_for_log(
    raw_payload: dict[str, Any], media_path: str | None
) -> dict[str, Any]:
    payload = json.loads(json.dumps(raw_payload))  # deep copy simples
    message = payload.get("data", {}).get("message")
    if isinstance(message, dict) and "base64" in message:
        message["base64"] = (
            f"<salvo em {media_path}>" if media_path else "<falha ao salvar>"
        )

    return payload


class WhatsAppService:
    async def send_text(
        self, number: str, text: str, instance_name: str | None = None
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.evolution_api_url}/message/sendText/"
                f"{instance_name or settings.evolution_instance_name}",
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

        if key.get("fromMe"):
            # mensagem que o próprio bot mandou, ecoada de volta pelo webhook -
            # ignora, senão ele responde a si mesmo em loop
            return

        instance_name = payload.instance or data.get("instance")
        business = await get_business_by_instance(instance_name, session)
        if business is None:
            logger.warning(
                "Evolution webhook: nenhum negócio ativo pra instância=%s",
                instance_name,
            )
            return

        raw_message = data.get("message")
        message: dict[str, Any] = raw_message if isinstance(raw_message, dict) else {}
        remote_jid = key.get("remoteJid") or key.get("remoteJidAlt")
        sender = remote_jid.split("@", 1)[0] if isinstance(remote_jid, str) else None
        message_type = data.get("messageType") or self.get_message_type(message)
        message_id = key.get("id") or data.get("id")

        logger.info(
            "Evolution message event: business=%s sender=%s type=%s text=%s message_id=%s",
            business.name,
            sender,
            message_type,
            self.get_text(message),
            message_id,
        )

        if sender is None or not isinstance(message_id, str):
            return

        phone_number = None
        if business.visibility == "private":
            # só número cadastrado em PhoneNumber.business_id recebe resposta
            phone_number = await get_active_phone_number_for_business(
                business.id, f"+{sender}", session
            )
            blocked = phone_number is None or await is_rate_limited(
                business.id, sender, session
            )
        else:
            blocked = await is_rate_limited(business.id, sender, session)

        image_message = message.get("imageMessage")
        image_base64 = (
            message.get("base64") if isinstance(image_message, dict) else None
        )

        media_path = None
        if image_base64:
            try:
                media_path = save_image(
                    message_id,
                    image_base64,
                    image_message.get("mimetype")
                    if isinstance(image_message, dict)
                    else None,
                )
            except Exception:
                logger.exception(
                    "Failed to save image to disk: message_id=%s", message_id
                )

        session.add(
            MessageLog(
                business_id=business.id,
                phone_number_id=phone_number.id if phone_number else None,
                sender=sender,
                external_message_id=message_id,
                message_type=message_type or "UNKNOWN",
                direction="INBOUND",
                payload=_sanitize_for_log(raw_payload, media_path),
                processed=False,
                blocked=blocked,
            )
        )
        await session.commit()

        logger.info(
            "Evolution rate limit check: sender=%s blocked=%s", sender, blocked
        )

        if blocked:
            return

        text = self.get_text(message) or (
            image_message.get("caption") if isinstance(image_message, dict) else None
        )

        try:
            system_prompt = await build_system_prompt(business, session)
            reply = await ask(system_prompt, text, image_base64)
        except Exception:
            logger.exception("Chatbot reply failed: sender=%s", sender)
            return

        try:
            reply_data = await self.send_text(
                sender, reply, business.evolution_instance_name
            )
        except Exception:
            # falha de rede/Evolution API não deve derrubar o webhook -
            # Evolution não deveria receber 500 por causa disso
            logger.exception("Send reply failed: sender=%s", sender)
            return

        session.add(
            MessageLog(
                business_id=business.id,
                sender=sender,
                external_message_id=reply_data.get("key", {}).get("id") or str(uuid4()),
                message_type="TEXT",
                direction="OUTBOUND",
                payload=reply_data,
                processed=True,
                blocked=False,
            )
        )
        await session.commit()

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
