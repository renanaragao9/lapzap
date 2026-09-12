from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserInput):
    password: str = Field(min_length=6, max_length=255)


class UserResponse(UserInput):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: int
    created_at: datetime
    updated_at: datetime
