import asyncio
import logging

import httpx
from conftest import create_business, create_user
from pytest import LogCaptureFixture
from sqlalchemy import select

from app.database.models.business import Business
from app.database.models.message_log import MessageLog
from app.database.models.phone_number import PhoneNumber
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
        return await session.scalar(
            select(MessageLog).order_by(MessageLog.id.desc()).limit(1)
        )
    return None


async def _count_logged_messages() -> int:
    async for session in get_test_session():
        rows = await session.scalars(select(MessageLog))
        return len(list(rows))
    return 0


def test_webhook_ignored_when_no_business_for_instance() -> None:
    # Nenhum Business com evolution_instance_name="lapzap-dev" cadastrado -
    # webhook não sabe pra quem responder, ignora sem logar nada.
    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))
    assert response.status_code == 200
    assert asyncio.run(_count_logged_messages()) == 0


def test_webhook_logs_message_for_any_sender_when_business_active() -> None:
    # Sem whitelist: qualquer número que mandar mensagem pro business ativo
    # é logado e respondido (rate-limit é a única barreira agora).
    business = asyncio.run(create_business(evolution_instance_name="lapzap-dev"))

    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))
    assert response.status_code == 200

    logged = asyncio.run(_get_logged_message())
    assert logged is not None
    assert logged.blocked is False
    assert logged.business_id == business.id
    assert logged.sender == "5585999999999"
    assert logged.external_message_id == "BAE5F001"


def test_webhook_blocks_sender_over_rate_limit() -> None:
    # RATE_LIMIT_PER_MINUTE=10 in .env: 10 prior inbound messages in the last
    # minute trip the limit, so the 11th is blocked - mesmo sem whitelist.
    business = asyncio.run(create_business(evolution_instance_name="lapzap-dev"))

    async def seed_prior_messages() -> None:
        async for session in get_test_session():
            for i in range(10):
                session.add(
                    MessageLog(
                        business_id=business.id,
                        sender="5585999999999",
                        external_message_id=f"seed-{i}",
                        message_type="TEXT",
                        direction="INBOUND",
                        payload={},
                        processed=True,
                        blocked=False,
                    )
                )
            await session.commit()

    asyncio.run(seed_prior_messages())

    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))
    assert response.status_code == 200

    logged = asyncio.run(_get_logged_message())
    assert logged is not None
    assert logged.blocked is True
    assert logged.business_id == business.id


def test_webhook_does_not_rate_limit_across_different_senders() -> None:
    business = asyncio.run(create_business(evolution_instance_name="lapzap-dev"))

    async def seed_prior_messages_from_other_sender() -> None:
        async for session in get_test_session():
            for i in range(10):
                session.add(
                    MessageLog(
                        business_id=business.id,
                        sender="5585900000000",
                        external_message_id=f"other-seed-{i}",
                        message_type="TEXT",
                        direction="INBOUND",
                        payload={},
                        processed=True,
                        blocked=False,
                    )
                )
            await session.commit()

    asyncio.run(seed_prior_messages_from_other_sender())

    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))
    assert response.status_code == 200

    logged = asyncio.run(_get_logged_message())
    assert logged is not None
    assert logged.blocked is False


def test_webhook_blocks_unlisted_sender_on_private_business() -> None:
    business = asyncio.run(
        create_business(evolution_instance_name="lapzap-dev", status="active")
    )

    async def make_private() -> None:
        async for session in get_test_session():
            biz = await session.get(Business, business.id)
            biz.visibility = "private"
            await session.commit()

    asyncio.run(make_private())

    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))
    assert response.status_code == 200

    logged = asyncio.run(_get_logged_message())
    assert logged is not None
    assert logged.blocked is True
    assert logged.phone_number_id is None


def test_webhook_allows_whitelisted_sender_on_private_business() -> None:
    business = asyncio.run(
        create_business(evolution_instance_name="lapzap-dev", status="active")
    )

    async def whitelist_sender() -> int:
        owner = await create_user(email="private-biz-owner@example.com")
        async for session in get_test_session():
            phone = PhoneNumber(
                user_id=owner.id,
                business_id=business.id,
                name="Cliente",
                phone_number="+5585999999999",
            )
            session.add(phone)
            await session.commit()
            await session.refresh(phone)
            return phone.id
        raise AssertionError("no session yielded")

    async def make_private() -> None:
        async for session in get_test_session():
            biz = await session.get(Business, business.id)
            biz.visibility = "private"
            await session.commit()

    asyncio.run(make_private())
    phone_id = asyncio.run(whitelist_sender())

    response = asyncio.run(post_webhook(TEXT_MESSAGE_PAYLOAD))
    assert response.status_code == 200

    logged = asyncio.run(_get_logged_message())
    assert logged is not None
    assert logged.blocked is False
    assert logged.phone_number_id == phone_id


def test_webhook_skips_persisting_message_without_id() -> None:
    asyncio.run(create_business(evolution_instance_name="lapzap-dev"))

    payload = {
        "event": "messages.upsert",
        "instance": "lapzap-dev",
        "data": {
            "key": {"remoteJid": "5585999999999@s.whatsapp.net"},
            "messageType": "conversation",
            "message": {"conversation": "sem id"},
        },
    }

    response = asyncio.run(post_webhook(payload))
    assert response.status_code == 200
    assert asyncio.run(_count_logged_messages()) == 0
