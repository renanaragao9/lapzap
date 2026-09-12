from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import get_current_user
from app.database.models.user import User
from app.database.session import get_session
from app.messages import service
from app.messages.schemas import MessageLogResponse

router = APIRouter(prefix="/api/v1/messages", tags=["Message logs"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[MessageLogResponse])
async def list_messages(
    current_user: CurrentUser,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[MessageLogResponse]:
    return await service.list_messages(current_user, session, limit)
