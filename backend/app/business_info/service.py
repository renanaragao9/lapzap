from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.service import get_owned_business_or_403
from app.business_info.schemas import BusinessInfoRequest
from app.database.models.business_info import BusinessInfo
from app.database.models.user import User


async def get_info(
    business_id: int, current_user: User, session: AsyncSession
) -> BusinessInfo:
    await get_owned_business_or_403(business_id, current_user, session)

    info = await session.scalar(
        select(BusinessInfo).where(BusinessInfo.business_id == business_id)
    )

    if info is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Negócio ainda não tem informações cadastradas."
        )

    return info


async def set_info(
    business_id: int,
    data: BusinessInfoRequest,
    current_user: User,
    session: AsyncSession,
) -> BusinessInfo:
    await get_owned_business_or_403(business_id, current_user, session)

    info = await session.scalar(
        select(BusinessInfo).where(BusinessInfo.business_id == business_id)
    )

    if info is None:
        info = BusinessInfo(business_id=business_id, content=data.content)
        session.add(info)
    else:
        info.content = data.content

    await session.commit()
    await session.refresh(info)

    return info


async def delete_info(
    business_id: int, current_user: User, session: AsyncSession
) -> None:
    await get_owned_business_or_403(business_id, current_user, session)

    info = await session.scalar(
        select(BusinessInfo).where(BusinessInfo.business_id == business_id)
    )

    if info is not None:
        await session.delete(info)
        await session.commit()
