from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_user
from app.business_integrations import service
from app.business_integrations.schemas import (
    BusinessIntegrationRequest,
    BusinessIntegrationResponse,
)
from app.database.models.user import User
from app.database.session import get_session

router = APIRouter(prefix="/api/v1/businesses", tags=["Business integrations"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get(
    "/{business_id}/integrations", response_model=list[BusinessIntegrationResponse]
)
async def list_integrations(
    business_id: int, current_user: CurrentUser, session: Session
) -> list[BusinessIntegrationResponse]:
    """Credenciais de APIs externas (Google Calendar, Outlook, genérica) que
    o negócio cadastrou - só guarda por enquanto, sem chamar a API ainda.
    """
    return await service.list_integrations(business_id, current_user, session)


@router.post(
    "/{business_id}/integrations",
    response_model=BusinessIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_integration(
    business_id: int,
    data: BusinessIntegrationRequest,
    current_user: CurrentUser,
    session: Session,
) -> BusinessIntegrationResponse:
    """Cadastra uma nova integração (credencial criptografada) - 409 se já
    existe uma com esse nome nesse negócio. Dono ou admin.
    """
    return await service.create_integration(business_id, data, current_user, session)


@router.put(
    "/{business_id}/integrations/{integration_id}",
    response_model=BusinessIntegrationResponse,
)
async def update_integration(
    business_id: int,
    integration_id: int,
    data: BusinessIntegrationRequest,
    current_user: CurrentUser,
    session: Session,
) -> BusinessIntegrationResponse:
    """Atualiza nome/tipo/host/email - secret omitido mantém o atual, só
    troca se vier preenchido. Dono ou admin.
    """
    return await service.update_integration(
        business_id, integration_id, data, current_user, session
    )


@router.delete(
    "/{business_id}/integrations/{integration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_integration(
    business_id: int,
    integration_id: int,
    current_user: CurrentUser,
    session: Session,
) -> None:
    """Remove a integração (e a credencial junto) - dono ou admin."""
    await service.delete_integration(business_id, integration_id, current_user, session)
