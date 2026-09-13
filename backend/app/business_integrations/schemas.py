from datetime import datetime

from pydantic import BaseModel, Field

from app.database.models.business_integration import IntegrationType


class BusinessIntegrationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: IntegrationType
    host: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    secret: str | None = None


class BusinessIntegrationResponse(BaseModel):
    id: int
    business_id: int
    name: str
    type: IntegrationType
    host: str | None
    email: str | None
    has_secret: bool
    created_at: datetime
    updated_at: datetime
