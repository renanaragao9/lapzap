from datetime import datetime

from pydantic import BaseModel


class BusinessSignupRequest(BaseModel):
    name: str
    business_type: str
    contact_phone_number: str
    plan: str


class BusinessResponse(BaseModel):
    id: int
    name: str
    business_type: str
    contact_phone_number: str
    plan: str
    status: str
    evolution_instance_name: str | None
    created_at: datetime


class BusinessActivateRequest(BaseModel):
    evolution_instance_name: str
