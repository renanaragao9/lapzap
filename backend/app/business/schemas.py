from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.database.models.business_integration import IntegrationType


class BusinessSignupRequest(BaseModel):
    name: str
    business_type: str
    contact_phone_number: str
    plan: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=255)


class BusinessResponse(BaseModel):
    id: int
    user_id: int | None
    name: str
    business_type: str
    contact_phone_number: str
    plan: str
    status: str
    visibility: str
    evolution_instance_name: str | None
    created_at: datetime


class BusinessVisibilityRequest(BaseModel):
    visibility: Literal["public", "private"]


class BusinessActivateRequest(BaseModel):
    evolution_instance_name: str | None = None


class CreateInstanceResponse(BaseModel):
    evolution_instance_name: str
    qrcode_base64: str


class BusinessInfoRequest(BaseModel):
    content: str = Field(max_length=20_000)


class BusinessInfoResponse(BaseModel):
    business_id: int
    content: str
    created_at: datetime
    updated_at: datetime


class BusinessIntegrationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: IntegrationType
    host: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    # senha ou api_key - mesmo campo, o "type" já diz o que é. Omitido =
    # mantém o segredo atual (update sem trocar).
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
