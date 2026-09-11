import asyncio
import logging

import httpx
from pytest import LogCaptureFixture

from app.main import app

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
