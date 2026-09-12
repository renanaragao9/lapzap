from datetime import datetime

from pydantic import BaseModel


class MessageLogResponse(BaseModel):
    id: int
    phone_number: str | None  # número de quem mandou/recebeu (MessageLog.sender)
    business_name: str | None
    message_type: str
    direction: str
    text: str | None
    processed: bool
    blocked: bool
    created_at: datetime
