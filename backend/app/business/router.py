from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_admin
from app.business.schemas import (
    BusinessActivateRequest,
    BusinessResponse,
    BusinessSignupRequest,
    CreateInstanceResponse,
)
from app.business.service import create_evolution_instance
from app.database.models.business import Business
from app.database.models.user import User
from app.database.session import get_session

router = APIRouter(prefix="/api/v1/businesses", tags=["Businesses"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]


@router.post(
    "/signup", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED
)
async def signup(data: BusinessSignupRequest, session: Session) -> Business:
    business = Business(
        name=data.name,
        business_type=data.business_type,
        contact_phone_number=data.contact_phone_number,
        plan=data.plan,
        status="pending_setup",
    )
    session.add(business)
    await session.commit()
    await session.refresh(business)
    return business


@router.get("", response_model=list[BusinessResponse])
async def list_pending(
    _current_admin: CurrentAdmin, session: Session
) -> list[Business]:
    result = await session.scalars(
        select(Business).order_by(Business.created_at.desc())
    )
    return list(result)


@router.post("/{business_id}/create-instance", response_model=CreateInstanceResponse)
async def create_instance(
    business_id: int,
    _current_admin: CurrentAdmin,
    session: Session,
) -> dict[str, str]:
    business = await session.get(Business, business_id)
    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Negócio não encontrado.")

    try:
        return await create_evolution_instance(business, session)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"Falha ao criar instância no Evolution API: {exc}",
        ) from exc


@router.post("/{business_id}/activate", response_model=BusinessResponse)
async def activate(
    business_id: int,
    data: BusinessActivateRequest,
    _current_admin: CurrentAdmin,
    session: Session,
) -> Business:
    business = await session.get(Business, business_id)

    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Negócio não encontrado.")

    business.evolution_instance_name = data.evolution_instance_name
    business.status = "active"
    await session.commit()
    await session.refresh(business)
    return business
