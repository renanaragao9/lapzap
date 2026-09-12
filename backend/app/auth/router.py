from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, TokenResponse
from app.auth.service import authenticate_user, get_current_user
from app.core.security import create_access_token
from app.database.models.user import User
from app.database.session import get_session
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: Session) -> TokenResponse:
    user = await authenticate_user(data.email, data.password, session)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    return current_user
