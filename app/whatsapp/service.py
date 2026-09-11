import logging
from typing import Any

from app.whatsapp.schemas import EvolutionWebhookPayload

logger = logging.getLogger(__name__)


class WhatsAppService:
    def process_webhook(
        self,
        payload: EvolutionWebhookPayload,
        raw_payload: dict[str, Any],
    ) -> None:
        logger.info("Evolution webhook payload received: %s", raw_payload)

        if not self.is_message_event(payload):
            logger.info("Evolution webhook event ignored: event=%s", payload.event)
            return

        data = payload.data or {}
        key = data.get("key") if isinstance(data.get("key"), dict) else {}
        message = (
            data.get("message") if isinstance(data.get("message"), dict) else {}
        )
        remote_jid = key.get("remoteJid") or key.get("remoteJidAlt")
        sender = remote_jid.split("@", 1)[0] if isinstance(remote_jid, str) else None
        message_type = data.get("messageType") or self.get_message_type(message)

        logger.info(
            "Evolution message event: instance=%s sender=%s type=%s text=%s message_id=%s",
            payload.instance or data.get("instance"),
            sender,
            message_type,
            self.get_text(message),
            key.get("id") or data.get("id"),
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
