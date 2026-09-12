from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_admin
from app.database.models.user import User
from app.database.session import get_session
from app.users import service
from app.users.schemas import UserCreate, UserInput, UserResponse

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    dependencies=[Depends(get_current_admin)],
)

CurrentAdmin = Annotated[User, Depends(get_current_admin)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[UserResponse])
async def list_users(session: Session) -> list[User]:
    return await service.list_users(session)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: Session) -> User:
    return await service.get_user_or_404(user_id, session)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, session: Session) -> User:
    return await service.create_user(data, session)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserInput, session: Session) -> User:
    return await service.update_user(user_id, data, session)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, admin: CurrentAdmin, session: Session) -> None:
    await service.delete_user(user_id, admin, session)
