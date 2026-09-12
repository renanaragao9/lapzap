from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.message_log import MessageLog
from app.database.models.phone_number import PhoneNumber
from app.database.models.user import User
from app.messages.schemas import MessageLogResponse
from app.whatsapp.service import WhatsAppService


def _message_dict(payload: dict[str, Any]) -> dict[str, Any]:
    raw_data = payload.get("data")
    data: dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}
    raw_message = data.get("message")
    return raw_message if isinstance(raw_message, dict) else {}


async def list_messages(
    current_user: User,
    session: AsyncSession,
    limit: int = 50,
) -> list[MessageLogResponse]:
    result = await session.execute(
        select(MessageLog, PhoneNumber.phone_number)
        .join(PhoneNumber, MessageLog.phone_number_id == PhoneNumber.id)
        .where(PhoneNumber.user_id == current_user.id)
        .order_by(MessageLog.created_at.desc())
        .limit(limit),
    )

    return [
        MessageLogResponse(
            id=log.id,
            phone_number=phone_number,
            message_type=log.message_type,
            direction=log.direction,
            text=WhatsAppService.get_text(_message_dict(log.payload)),
            processed=log.processed,
            blocked=log.blocked,
            created_at=log.created_at,
        )
        for log, phone_number in result.all()
    ]
