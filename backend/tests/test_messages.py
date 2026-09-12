import asyncio

from conftest import auth_headers, create_business, create_user, request


def webhook_payload(instance: str, remote_jid: str, text: str, message_id: str) -> dict:
    return {
        "event": "messages.upsert",
        "instance": instance,
        "data": {
            "key": {"remoteJid": remote_jid, "id": message_id},
            "messageType": "conversation",
            "message": {"conversation": text},
        },
    }


def test_list_messages_requires_auth() -> None:
    response = asyncio.run(request("GET", "/api/v1/messages"))
    assert response.status_code == 401


def test_list_messages_scoped_to_business_owner() -> None:
    async def scenario() -> None:
        owner = await create_user(email="owner@example.com")
        other = await create_user(email="other@example.com")
        owner_headers = auth_headers(owner.id)
        other_headers = auth_headers(other.id)

        await create_business(evolution_instance_name="owner-biz", user_id=owner.id)
        await create_business(evolution_instance_name="other-biz", user_id=other.id)

        await request(
            "POST",
            "/api/v1/webhooks/whatsapp",
            json=webhook_payload(
                "owner-biz", "5585999999999@s.whatsapp.net", "Oi, dono!", "OWNER-MSG-1"
            ),
        )
        await request(
            "POST",
            "/api/v1/webhooks/whatsapp",
            json=webhook_payload(
                "other-biz", "5585988888888@s.whatsapp.net", "Oi, outro!", "OTHER-MSG-1"
            ),
        )

        owner_messages = await request(
            "GET", "/api/v1/messages", headers=owner_headers
        )
        assert owner_messages.status_code == 200
        owner_body = owner_messages.json()
        assert len(owner_body) == 1
        assert owner_body[0]["phone_number"] == "5585999999999"
        assert owner_body[0]["business_name"] == "Test Business"
        assert owner_body[0]["text"] == "Oi, dono!"
        assert owner_body[0]["blocked"] is False

        other_messages = await request(
            "GET", "/api/v1/messages", headers=other_headers
        )
        assert other_messages.status_code == 200
        other_body = other_messages.json()
        assert len(other_body) == 1
        assert other_body[0]["phone_number"] == "5585988888888"

    asyncio.run(scenario())


def test_list_messages_excludes_business_without_owner() -> None:
    async def scenario() -> None:
        owner = await create_user(email="owner2@example.com")
        owner_headers = auth_headers(owner.id)

        # negócio sem user_id vinculado (fluxo de cadastro público, ainda não
        # ligado a nenhuma conta) - mensagem existe mas não aparece pra
        # ninguém até um admin vincular o dono.
        await create_business(evolution_instance_name="unclaimed-biz", user_id=None)

        await request(
            "POST",
            "/api/v1/webhooks/whatsapp",
            json=webhook_payload(
                "unclaimed-biz",
                "5585900000000@s.whatsapp.net",
                "Estranho",
                "STRANGER-MSG-1",
            ),
        )

        response = await request("GET", "/api/v1/messages", headers=owner_headers)
        assert response.status_code == 200
        assert response.json() == []

    asyncio.run(scenario())
