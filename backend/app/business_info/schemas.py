from datetime import datetime

from pydantic import BaseModel, Field


class BusinessInfoRequest(BaseModel):
    content: str = Field(max_length=20_000)


class BusinessInfoResponse(BaseModel):
    business_id: int
    content: str
    created_at: datetime
    updated_at: datetime
