from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PhoneNumberInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(
        min_length=8,
        max_length=20,
        pattern=r"^\+[1-9]\d{7,14}$",
    )
    name: str = Field(min_length=1, max_length=255)


class PhoneNumberResponse(PhoneNumberInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
