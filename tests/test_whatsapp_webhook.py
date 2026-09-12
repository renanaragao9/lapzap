import asyncio
import logging

import httpx
from pytest import LogCaptureFixture
from sqlalchemy import select

from app.core.security import hash_password
from app.database.models.message_log import MessageLog
from app.database.models.phone_number import PhoneNumber
from app.database.models.user import User
from app.database.session import get_session
from app.main import app

# app.dependency_overrides[get_session] is installed by conftest.py (autouse
# import) and points at the shared in-memory test database.
get_test_session = app.dependency_overrides[get_session]

TEXT_MESSAGE_PAYLOAD = {
    "event": "messages.upsert",
    "instance": "lapzap-dev",
    "data": {
        "key": {
            "remoteJid": "5585999999999@s.whatsapp.net",
            "id": "BAE5F001",
        },
        "messageType": "conversation",
        "message": {"conversation": "Olá, LapZap!"},
    },
}


async def post_webhook(payload: dict[str, object]) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.post("/api/v1/webhooks/whatsapp", json=payload)


def test_webhook_returns_ok_for_text_message(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.whatsapp.service")
    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "Olá, LapZap!" in caplog.text


def test_webhook_accepts_incomplete_payload() -> None:
    response = asyncio.run(post_webhook({"event": "connection.update"}))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_accepts_event_with_list_data() -> None:
    response = asyncio.run(
        post_webhook({"event": "messages.set", "data": []}),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def _get_logged_message() -> MessageLog | None:
    async for session in get_test_session():
        return await session.scalar(select(MessageLog))
    return None


def test_webhook_logs_and_blocks_unauthorized_sender() -> None:
    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))
    assert response.status_code == 200

    logged = asyncio.run(_get_logged_message())
    assert logged is not None
    assert logged.blocked is True
    assert logged.phone_number_id is None
    assert logged.external_message_id == "BAE5F001"


def test_webhook_logs_authorized_sender_as_not_blocked() -> None:
    async def seed() -> None:
        async for session in get_test_session():
            user = User(
                name="Webhook Owner",
                email="webhook@example.com",
                password_hash=hash_password("123456"),
                is_active=True,
            )
            session.add(user)
            await session.flush()
            session.add(
                PhoneNumber(
                    user_id=user.id,
                    name="Autorizado",
                    phone_number="+5585999999999",
                )
            )
            await session.commit()

    asyncio.run(seed())

    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))
    assert response.status_code == 200

    logged = asyncio.run(_get_logged_message())
    assert logged is not None
    assert logged.blocked is False
    assert logged.phone_number_id is not None
