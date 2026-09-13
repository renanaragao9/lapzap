from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_admin, get_current_user
from app.business.schemas import (
    BusinessActivateRequest,
    BusinessResponse,
    BusinessSignupRequest,
    BusinessVisibilityRequest,
    CreateInstanceResponse,
)
from app.business.service import create_evolution_instance, get_owned_business_or_403
from app.core.security import hash_password
from app.database.models.business import Business
from app.database.models.user import User
from app.database.session import get_session

router = APIRouter(prefix="/api/v1/businesses", tags=["Businesses"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/signup", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED
)
async def signup(data: BusinessSignupRequest, session: Session) -> Business:
    """Cadastro público (sem login) - cria a conta do dono e o negócio juntos,
    "pending_setup" e sem instância. 409 se e-mail ou telefone já existem.
    """
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
    """Lista todos os negócios (qualquer status) - admin, tela /negocios."""
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
    business = await get_owned_business_or_403(business_id, current_user, session)

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
    business = await get_owned_business_or_403(business_id, current_user, session)

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
