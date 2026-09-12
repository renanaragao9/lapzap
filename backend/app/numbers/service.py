from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models.business import Business
from app.database.models.message_log import MessageLog
from app.database.models.phone_number import PhoneNumber
from app.database.models.user import User
from app.numbers.schemas import PhoneNumberInput


def _br_number_variants(phone_number: str) -> list[str]:
    """BR: WhatsApp manda/recebe número com ou sem o 9º dígito móvel
    (ex: +5585997304827 vs +558597304827 são o mesmo número) - gera as duas
    formas pra não perder o match por causa disso.
    """
    digits = phone_number.lstrip("+")
    variants = {phone_number}

    if digits.startswith("55") and len(digits) in (12, 13):
        ddi, ddd, rest = digits[:2], digits[2:4], digits[4:]
        if len(rest) == 8:
            variants.add(f"+{ddi}{ddd}9{rest}")
        elif len(rest) == 9 and rest[0] == "9":
            variants.add(f"+{ddi}{ddd}{rest[1:]}")

    return list(variants)


async def get_active_phone_number_for_business(
    business_id: int,
    phone_number: str,
    session: AsyncSession,
) -> PhoneNumber | None:
    """Whitelist por negócio - só importa quando Business.visibility ==
    "private" (ver whatsapp/service.py).
    """
    return await session.scalar(
        select(PhoneNumber).where(
            PhoneNumber.business_id == business_id,
            PhoneNumber.phone_number.in_(_br_number_variants(phone_number)),
            PhoneNumber.is_active.is_(True),
        ),
    )


async def is_rate_limited(phone_number_id: int, session: AsyncSession) -> bool:
    window_start = datetime.now(timezone.utc) - timedelta(minutes=1)
    message_count = await session.scalar(
        select(func.count())
        .select_from(MessageLog)
        .where(
            MessageLog.phone_number_id == phone_number_id,
            MessageLog.direction == "INBOUND",
            MessageLog.created_at >= window_start,
        ),
    )
    return (message_count or 0) >= settings.rate_limit_per_minute


async def get_owned_business_or_403(
    business_id: int,
    current_user: User,
    session: AsyncSession,
) -> Business:
    business = await session.get(Business, business_id)
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Negócio não encontrado.")
    if business.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Sem permissão pra esse negócio."
        )
    return business


async def get_owned_phone_number_or_404(
    phone_number_id: int,
    current_user: User,
    session: AsyncSession,
) -> PhoneNumber:
    phone_number = await session.scalar(
        select(PhoneNumber)
        .join(Business, PhoneNumber.business_id == Business.id)
        .where(
            PhoneNumber.id == phone_number_id,
            Business.user_id == current_user.id,
        ),
    )

    if phone_number is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Número autorizado não encontrado.",
        )

    return phone_number


async def list_phone_numbers(
    business_id: int,
    current_user: User,
    session: AsyncSession,
) -> list[PhoneNumber]:
    await get_owned_business_or_403(business_id, current_user, session)
    result = await session.scalars(
        select(PhoneNumber)
        .where(PhoneNumber.business_id == business_id)
        .order_by(PhoneNumber.id),
    )
    return list(result)


async def create_phone_number(
    data: PhoneNumberInput,
    current_user: User,
    session: AsyncSession,
) -> PhoneNumber:
    await get_owned_business_or_403(data.business_id, current_user, session)

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
            detail="Este número já está autorizado nesse negócio.",
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
            detail="Este número já está autorizado nesse negócio.",
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
