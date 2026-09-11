from typing import Any

from pydantic import BaseModel, ConfigDict


class EvolutionWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    event: str | None = None
    instance: str | None = None
    data: Any | None = None


class WebhookResponse(BaseModel):
    status: str = "ok"
