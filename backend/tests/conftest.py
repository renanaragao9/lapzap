import asyncio
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.database.base import Base
from app.database.models.business import Business
from app.database.models.business_hours import (
    BusinessHours,  # noqa: F401 (register mapping)
)
from app.database.models.message_log import MessageLog  # noqa: F401 (register mapping)
from app.database.models.phone_number import (
    PhoneNumber,  # noqa: F401 (register mapping)
)
from app.database.models.user import User
from app.database.session import get_session
from app.main import app

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
    is_admin: bool = False,
) -> User:
    async with session_factory() as session:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_active=is_active,
            is_admin=is_admin,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def auth_headers(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


async def create_business(
    evolution_instance_name: str,
    user_id: int | None = None,
    name: str = "Test Business",
    business_type: str = "generico",
    status: str = "active",
) -> Business:
    async with session_factory() as session:
        business = Business(
            user_id=user_id,
            name=name,
            business_type=business_type,
            contact_phone_number="+5585999999999",
            plan="starter",
            status=status,
            evolution_instance_name=evolution_instance_name,
        )
        session.add(business)
        await session.commit()
        await session.refresh(business)
        return business


async def request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.request(method, url, **kwargs)
