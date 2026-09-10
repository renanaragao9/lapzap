from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password
from app.database.models.user import User
from app.database.session import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authenticate_user(
    email: str,
    password: str,
    session: AsyncSession,
) -> User | None:
    user = await session.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(password, user.password_hash):
        return None

    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError:
        raise credentials_exception() from None

    subject = payload.get("sub")

    if not isinstance(subject, str):
        raise credentials_exception()

    try:
        user_id = int(subject)
    except ValueError:
        raise credentials_exception() from None

    user = await session.get(User, user_id)
    
    if user is None or not user.is_active:
        raise credentials_exception()

    return user
