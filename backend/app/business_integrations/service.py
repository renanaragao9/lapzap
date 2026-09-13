from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.business.service import get_owned_business_or_403
from app.business_integrations.schemas import (
    BusinessIntegrationRequest,
    BusinessIntegrationResponse,
)
from app.core.security import encrypt_secret
from app.database.models.business_integration import BusinessIntegration
from app.database.models.user import User

_DUPLICATE_NAME_DETAIL = "Já existe uma integração com esse nome pra esse negócio."


def _to_response(integration: BusinessIntegration) -> BusinessIntegrationResponse:
    return BusinessIntegrationResponse(
        id=integration.id,
        business_id=integration.business_id,
        name=integration.name,
        type=integration.type,
        host=integration.host,
        email=integration.email,
        has_secret=bool(integration.encrypted_secret),
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )


async def get_owned_integration_or_404(
    business_id: int,
    integration_id: int,
    current_user: User,
    session: AsyncSession,
) -> BusinessIntegration:
    await get_owned_business_or_403(business_id, current_user, session)
    integration = await session.scalar(
        select(BusinessIntegration).where(
            BusinessIntegration.id == integration_id,
            BusinessIntegration.business_id == business_id,
        )
    )
    if integration is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Integração não encontrada.")
    return integration


async def list_integrations(
    business_id: int, current_user: User, session: AsyncSession
) -> list[BusinessIntegrationResponse]:
    await get_owned_business_or_403(business_id, current_user, session)
    result = await session.scalars(
        select(BusinessIntegration)
        .where(BusinessIntegration.business_id == business_id)
        .order_by(BusinessIntegration.name)
    )
    return [_to_response(i) for i in result]


async def create_integration(
    business_id: int,
    data: BusinessIntegrationRequest,
    current_user: User,
    session: AsyncSession,
) -> BusinessIntegrationResponse:
    await get_owned_business_or_403(business_id, current_user, session)

    integration = BusinessIntegration(
        business_id=business_id,
        name=data.name,
        type=data.type,
        host=data.host,
        email=data.email,
        encrypted_secret=encrypt_secret(data.secret) if data.secret else None,
    )
    session.add(integration)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, _DUPLICATE_NAME_DETAIL) from None

    await session.refresh(integration)
    return _to_response(integration)


async def update_integration(
    business_id: int,
    integration_id: int,
    data: BusinessIntegrationRequest,
    current_user: User,
    session: AsyncSession,
) -> BusinessIntegrationResponse:
    integration = await get_owned_integration_or_404(
        business_id, integration_id, current_user, session
    )
    integration.name = data.name
    integration.type = data.type
    integration.host = data.host
    integration.email = data.email

    if data.secret:
        integration.encrypted_secret = encrypt_secret(data.secret)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, _DUPLICATE_NAME_DETAIL) from None

    await session.refresh(integration)
    return _to_response(integration)


async def delete_integration(
    business_id: int,
    integration_id: int,
    current_user: User,
    session: AsyncSession,
) -> None:
    integration = await get_owned_integration_or_404(
        business_id, integration_id, current_user, session
    )
    await session.delete(integration)
    await session.commit()
