from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.phone_number import PhoneNumber
from app.database.models.user import User
from app.numbers.schemas import PhoneNumberInput


async def is_phone_authorized(
    phone_number: str,
    session: AsyncSession,
) -> bool:
    phone_number_id = await session.scalar(
        select(PhoneNumber.id).where(
            PhoneNumber.phone_number == phone_number,
            PhoneNumber.is_active.is_(True),
        ),
    )
    return phone_number_id is not None


async def get_owned_phone_number_or_404(
    phone_number_id: int,
    current_user: User,
    session: AsyncSession,
) -> PhoneNumber:
    phone_number = await session.scalar(
        select(PhoneNumber).where(
            PhoneNumber.id == phone_number_id,
            PhoneNumber.user_id == current_user.id,
        ),
    )

    if phone_number is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Número autorizado não encontrado.",
        )

    return phone_number


async def list_phone_numbers(
    current_user: User, session: AsyncSession
) -> list[PhoneNumber]:
    result = await session.scalars(
        select(PhoneNumber)
        .where(PhoneNumber.user_id == current_user.id)
        .order_by(PhoneNumber.id),
    )
    return list(result)


async def create_phone_number(
    data: PhoneNumberInput,
    current_user: User,
    session: AsyncSession,
) -> PhoneNumber:
    phone_number = PhoneNumber(
        user_id=current_user.id,
        **data.model_dump(),
    )
    session.add(phone_number)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este número já está autorizado.",
        ) from None

    await session.refresh(phone_number)
    return phone_number


async def update_phone_number(
    phone_number_id: int,
    data: PhoneNumberInput,
    current_user: User,
    session: AsyncSession,
) -> PhoneNumber:
    phone_number = await get_owned_phone_number_or_404(
        phone_number_id,
        current_user,
        session,
    )
    phone_number.phone_number = data.phone_number
    phone_number.name = data.name

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este número já está autorizado.",
        ) from None

    await session.refresh(phone_number)
    return phone_number


async def delete_phone_number(
    phone_number_id: int,
    current_user: User,
    session: AsyncSession,
) -> None:
    phone_number = await get_owned_phone_number_or_404(
        phone_number_id,
        current_user,
        session,
    )
    await session.delete(phone_number)
    await session.commit()
