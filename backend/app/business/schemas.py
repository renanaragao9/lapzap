from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class BusinessSignupRequest(BaseModel):
    name: str
    business_type: str
    contact_phone_number: str
    plan: str


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
    evolution_instance_name: str


class CreateInstanceResponse(BaseModel):
    evolution_instance_name: str
    qrcode_base64: str
