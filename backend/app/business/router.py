from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_admin, get_current_user
from app.business.schemas import (
    BusinessActivateRequest,
    BusinessInfoRequest,
    BusinessInfoResponse,
    BusinessIntegrationRequest,
    BusinessIntegrationResponse,
    BusinessResponse,
    BusinessSignupRequest,
    BusinessVisibilityRequest,
    CreateInstanceResponse,
)
from app.business.service import create_evolution_instance
from app.core.security import encrypt_secret, hash_password
from app.database.models.business import Business
from app.database.models.business_info import BusinessInfo
from app.database.models.business_integration import BusinessIntegration
from app.database.models.user import User
from app.database.session import get_session

router = APIRouter(prefix="/api/v1/businesses", tags=["Businesses"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
CurrentUser = Annotated[User, Depends(get_current_user)]


async def _get_owned_business_or_403(
    business_id: int, current_user: User, session: AsyncSession
) -> Business:
    business = await session.get(Business, business_id)

    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Negócio não encontrado.")

    if business.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Sem permissão pra esse negócio."
        )

    return business


@router.post(
    "/signup", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED
)
async def signup(data: BusinessSignupRequest, session: Session) -> Business:
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=True,
        is_admin=False,
    )
    business = Business(
        name=data.name,
        business_type=data.business_type,
        contact_phone_number=data.contact_phone_number,
        plan=data.plan,
        status="pending_setup",
        user=user,
    )
    session.add(business)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "uq_businesses_contact_phone_number" in str(exc.orig):
            detail = "Esse número de WhatsApp já está cadastrado em outro negócio."
        else:
            detail = "Este e-mail já está cadastrado."
        raise HTTPException(status.HTTP_409_CONFLICT, detail) from None

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


@router.get("/mine", response_model=list[BusinessResponse])
async def list_mine(current_user: CurrentUser, session: Session) -> list[Business]:
    """Negócios do usuário logado - usado pra achar o business_id certo na
    tela de números autorizados, sem precisar ser admin.
    """
    result = await session.scalars(
        select(Business)
        .where(Business.user_id == current_user.id)
        .order_by(Business.created_at.desc()),
    )
    return list(result)


@router.post("/{business_id}/create-instance", response_model=CreateInstanceResponse)
async def create_instance(
    business_id: int,
    current_user: CurrentUser,
    session: Session,
) -> dict[str, str]:
    """Dono do negócio cria a própria instância e escaneia o QR code - ainda
    fica "pending_setup" até o admin aprovar (ver activate).
    """
    business = await _get_owned_business_or_403(business_id, current_user, session)

    try:
        return await create_evolution_instance(business, session)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"Falha ao criar instância no Evolution API: {exc}",
        ) from exc


@router.post("/{business_id}/visibility", response_model=BusinessResponse)
async def set_visibility(
    business_id: int,
    data: BusinessVisibilityRequest,
    current_user: CurrentUser,
    session: Session,
) -> Business:
    """O próprio negócio decide se é público (qualquer cliente recebe
    resposta) ou privado (só número em PhoneNumber.business_id) - dono ou
    admin pode mudar.
    """
    business = await _get_owned_business_or_403(business_id, current_user, session)

    business.visibility = data.visibility
    await session.commit()
    await session.refresh(business)
    return business


@router.post("/{business_id}/activate", response_model=BusinessResponse)
async def activate(
    business_id: int,
    data: BusinessActivateRequest,
    _current_admin: CurrentAdmin,
    session: Session,
) -> Business:
    """Aprovação final - só admin. Se o dono já criou a instância sozinho
    (create-instance), não precisa mandar evolution_instance_name de novo.
    """
    business = await session.get(Business, business_id)

    if business is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Negócio não encontrado.")

    if data.evolution_instance_name:
        business.evolution_instance_name = data.evolution_instance_name

    if not business.evolution_instance_name:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Negócio ainda não tem instância criada - crie uma ou informe o nome.",
        )

    business.status = "active"
    await session.commit()
    await session.refresh(business)
    return business


@router.get("/{business_id}/info", response_model=BusinessInfoResponse)
async def get_info(
    business_id: int, current_user: CurrentUser, session: Session
) -> BusinessInfo:
    await _get_owned_business_or_403(business_id, current_user, session)

    info = await session.scalar(
        select(BusinessInfo).where(BusinessInfo.business_id == business_id)
    )

    if info is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Negócio ainda não tem informações cadastradas."
        )

    return info


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
    await _get_owned_business_or_403(business_id, current_user, session)

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


@router.delete("/{business_id}/info", status_code=status.HTTP_204_NO_CONTENT)
async def delete_info(
    business_id: int, current_user: CurrentUser, session: Session
) -> None:
    await _get_owned_business_or_403(business_id, current_user, session)

    info = await session.scalar(
        select(BusinessInfo).where(BusinessInfo.business_id == business_id)
    )

    if info is not None:
        await session.delete(info)
        await session.commit()


def _integration_to_response(
    integration: BusinessIntegration,
) -> BusinessIntegrationResponse:
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


@router.get(
    "/{business_id}/integrations", response_model=list[BusinessIntegrationResponse]
)
async def list_integrations(
    business_id: int, current_user: CurrentUser, session: Session
) -> list[BusinessIntegrationResponse]:
    """Credenciais de APIs externas (Google Calendar, Outlook, genérica) que
    o negócio cadastrou - só guarda por enquanto, sem chamar a API ainda.
    """
    await _get_owned_business_or_403(business_id, current_user, session)
    result = await session.scalars(
        select(BusinessIntegration)
        .where(BusinessIntegration.business_id == business_id)
        .order_by(BusinessIntegration.name)
    )
    return [_integration_to_response(i) for i in result]


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
    await _get_owned_business_or_403(business_id, current_user, session)

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
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Já existe uma integração com esse nome pra esse negócio.",
        ) from None

    await session.refresh(integration)
    return _integration_to_response(integration)


async def _get_owned_integration_or_404(
    business_id: int, integration_id: int, current_user: User, session: AsyncSession
) -> BusinessIntegration:
    await _get_owned_business_or_403(business_id, current_user, session)
    integration = await session.scalar(
        select(BusinessIntegration).where(
            BusinessIntegration.id == integration_id,
            BusinessIntegration.business_id == business_id,
        )
    )
    if integration is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Integração não encontrada.")
    return integration


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
    integration = await _get_owned_integration_or_404(
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
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Já existe uma integração com esse nome pra esse negócio.",
        ) from None

    await session.refresh(integration)
    return _integration_to_response(integration)


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
    integration = await _get_owned_integration_or_404(
        business_id, integration_id, current_user, session
    )
    await session.delete(integration)
    await session.commit()
