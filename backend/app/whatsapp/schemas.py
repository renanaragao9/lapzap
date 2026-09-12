from typing import Any

from pydantic import BaseModel, ConfigDict


class EvolutionWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    event: str | None = None
    instance: str | None = None
    data: Any | None = None


class WebhookResponse(BaseModel):
    status: str = "ok"


class BroadcastRequest(BaseModel):
    numbers: list[str]
    text: str
    delay_seconds: float = 2.0


class BroadcastResult(BaseModel):
    number: str
    status: str
    detail: str | None = None
