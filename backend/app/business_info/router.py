from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_user
from app.business_info import service
from app.business_info.schemas import BusinessInfoRequest, BusinessInfoResponse
from app.database.models.business_info import BusinessInfo
from app.database.models.user import User
from app.database.session import get_session

router = APIRouter(prefix="/api/v1/businesses", tags=["Business info"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/{business_id}/info", response_model=BusinessInfoResponse)
async def get_info(
    business_id: int, current_user: CurrentUser, session: Session
) -> BusinessInfo:
    """Lê o texto em markdown cadastrado - 404 se o negócio ainda não
    preencheu nada. Dono ou admin.
    """
    return await service.get_info(business_id, current_user, session)


@router.put("/{business_id}/info", response_model=BusinessInfoResponse)
async def set_info(
    business_id: int,
    data: BusinessInfoRequest,
    current_user: CurrentUser,
    session: Session,
) -> BusinessInfo:
    """Texto livre em markdown que o dono preenche pra dar mais contexto ao
    LLM (ver build_system_prompt) - cria ou atualiza, dono ou admin.
    """
    return await service.set_info(business_id, data, current_user, session)


@router.delete("/{business_id}/info", status_code=status.HTTP_204_NO_CONTENT)
async def delete_info(
    business_id: int, current_user: CurrentUser, session: Session
) -> None:
    """Apaga o texto em markdown do negócio (se existir) - dono ou admin."""
    await service.delete_info(business_id, current_user, session)
