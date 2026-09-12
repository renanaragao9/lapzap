from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database.models.phone_number import PhoneNumber
from app.database.models.user import User
from app.users.schemas import UserCreate, UserInput


async def list_users(session: AsyncSession) -> list[User]:
    result = await session.scalars(select(User).order_by(User.id))
    return list(result)


async def get_user_or_404(user_id: int, session: AsyncSession) -> User:
    user = await session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    return user


async def create_user(data: UserCreate, session: AsyncSession) -> User:
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=data.is_active,
        is_admin=data.is_admin,
    )
    session.add(user)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        ) from None

    await session.refresh(user)
    return user


async def update_user(user_id: int, data: UserInput, session: AsyncSession) -> User:
    user = await get_user_or_404(user_id, session)
    user.name = data.name
    user.email = data.email
    user.is_active = data.is_active
    user.is_admin = data.is_admin

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        ) from None

    await session.refresh(user)
    return user


async def delete_user(user_id: int, current_admin: User, session: AsyncSession) -> None:
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode remover sua própria conta.",
        )

    user = await get_user_or_404(user_id, session)

    has_numbers = await session.scalar(
        select(PhoneNumber.id).where(PhoneNumber.user_id == user.id).limit(1),
    )

    if has_numbers is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Remova os números autorizados deste usuário antes de excluí-lo.",
        )

    await session.delete(user)
    await session.commit()
