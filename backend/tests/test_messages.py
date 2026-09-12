import asyncio

from conftest import auth_headers, create_user, request


def webhook_payload(remote_jid: str, text: str, message_id: str) -> dict:
    return {
        "event": "messages.upsert",
        "instance": "lapzap-dev",
        "data": {
            "key": {"remoteJid": remote_jid, "id": message_id},
            "messageType": "conversation",
            "message": {"conversation": text},
        },
    }


async def create_phone_number(phone_number: str, headers: dict) -> None:
    response = await request(
        "POST",
        "/api/v1/numbers",
        json={"phone_number": phone_number, "name": "Owner"},
        headers=headers,
    )
    assert response.status_code == 201


def test_list_messages_requires_auth() -> None:
    response = asyncio.run(request("GET", "/api/v1/messages"))
    assert response.status_code == 401


def test_list_messages_scoped_to_owner_and_extracts_text() -> None:
    async def scenario() -> None:
        owner = await create_user(email="owner@example.com")
        other = await create_user(email="other@example.com")
        owner_headers = auth_headers(owner.id)
        other_headers = auth_headers(other.id)

        await create_phone_number("+5585999999999", owner_headers)
        await create_phone_number("+5585988888888", other_headers)

        await request(
            "POST",
            "/api/v1/webhooks/whatsapp",
            json=webhook_payload(
                "5585999999999@s.whatsapp.net", "Oi, dono!", "OWNER-MSG-1"
            ),
        )
        await request(
            "POST",
            "/api/v1/webhooks/whatsapp",
            json=webhook_payload(
                "5585988888888@s.whatsapp.net", "Oi, outro!", "OTHER-MSG-1"
            ),
        )

        owner_messages = await request(
            "GET", "/api/v1/messages", headers=owner_headers
        )
        assert owner_messages.status_code == 200
        owner_body = owner_messages.json()
        assert len(owner_body) == 1
        assert owner_body[0]["phone_number"] == "+5585999999999"
        assert owner_body[0]["text"] == "Oi, dono!"
        assert owner_body[0]["blocked"] is False

        other_messages = await request(
            "GET", "/api/v1/messages", headers=other_headers
        )
        assert other_messages.status_code == 200
        other_body = other_messages.json()
        assert len(other_body) == 1
        assert other_body[0]["phone_number"] == "+5585988888888"

    asyncio.run(scenario())


def test_list_messages_excludes_unauthorized_sender() -> None:
    async def scenario() -> None:
        owner = await create_user(email="owner2@example.com")
        owner_headers = auth_headers(owner.id)
        await create_phone_number("+5585999999999", owner_headers)

        # No phone_number authorized for this sender: logged with
        # phone_number_id=NULL, blocked=True, and excluded from every user's
        # list (nothing to scope it to).
        await request(
            "POST",
            "/api/v1/webhooks/whatsapp",
            json=webhook_payload(
                "5585900000000@s.whatsapp.net", "Estranho", "STRANGER-MSG-1"
            ),
        )

        response = await request("GET", "/api/v1/messages", headers=owner_headers)
        assert response.status_code == 200
        assert response.json() == []

    asyncio.run(scenario())
