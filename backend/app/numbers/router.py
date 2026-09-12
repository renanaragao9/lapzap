from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_user
from app.database.models.phone_number import PhoneNumber
from app.database.models.user import User
from app.database.session import get_session
from app.numbers import service
from app.numbers.schemas import PhoneNumberInput, PhoneNumberResponse

router = APIRouter(prefix="/api/v1/numbers", tags=["Authorized numbers"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "", response_model=PhoneNumberResponse, status_code=status.HTTP_201_CREATED
)
async def create_phone_number(
    data: PhoneNumberInput,
    current_user: CurrentUser,
    session: Session,
) -> PhoneNumber:
    return await service.create_phone_number(data, current_user, session)


@router.get("", response_model=list[PhoneNumberResponse])
async def list_phone_numbers(
    current_user: CurrentUser,
    session: Session,
    business_id: Annotated[int, Query()],
) -> list[PhoneNumber]:
    return await service.list_phone_numbers(business_id, current_user, session)


@router.get("/{phone_number_id}", response_model=PhoneNumberResponse)
async def get_phone_number(
    phone_number_id: int,
    current_user: CurrentUser,
    session: Session,
) -> PhoneNumber:
    return await service.get_owned_phone_number_or_404(
        phone_number_id,
        current_user,
        session,
    )


@router.put("/{phone_number_id}", response_model=PhoneNumberResponse)
async def update_phone_number(
    phone_number_id: int,
    data: PhoneNumberInput,
    current_user: CurrentUser,
    session: Session,
) -> PhoneNumber:
    return await service.update_phone_number(
        phone_number_id,
        data,
        current_user,
        session,
    )


@router.delete("/{phone_number_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_phone_number(
    phone_number_id: int,
    current_user: CurrentUser,
    session: Session,
) -> None:
    await service.delete_phone_number(phone_number_id, current_user, session)
