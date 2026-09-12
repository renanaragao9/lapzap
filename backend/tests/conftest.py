import asyncio
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.database.base import Base
from app.database.models.message_log import MessageLog  # noqa: F401 (register mapping)
from app.database.models.phone_number import (
    PhoneNumber,  # noqa: F401 (register mapping)
)
from app.database.models.user import User
from app.database.session import get_session
from app.main import app

# Single shared in-memory connection: StaticPool keeps every session on the
# same SQLite connection, otherwise each would get its own empty :memory: db.
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def _test_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


app.dependency_overrides[get_session] = _test_session


@pytest.fixture(autouse=True)
def _reset_database() -> None:
    async def reset() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(reset())


async def create_user(
    email: str = "user@example.com",
    password: str = "123456",
    name: str = "Test User",
    is_active: bool = True,
) -> User:
    async with session_factory() as session:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_active=is_active,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def auth_headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


async def request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.request(method, url, **kwargs)
