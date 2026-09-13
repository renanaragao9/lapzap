from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


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
