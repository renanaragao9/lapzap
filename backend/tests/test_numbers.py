import asyncio

from conftest import auth_headers, create_user, request

PHONE_PAYLOAD = {"phone_number": "+5585999999999", "name": "Renan"}


def test_create_phone_number() -> None:
    async def scenario() -> None:
        user = await create_user(email="create@example.com")

        response = await request(
            "POST",
            "/api/v1/numbers",
            json=PHONE_PAYLOAD,
            headers=auth_headers(user.id),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["phone_number"] == PHONE_PAYLOAD["phone_number"]
        assert body["is_active"] is True

    asyncio.run(scenario())


def test_create_phone_number_rejects_invalid_format() -> None:
    async def scenario() -> None:
        user = await create_user(email="invalid@example.com")

        response = await request(
            "POST",
            "/api/v1/numbers",
            json={"phone_number": "5585999999999", "name": "Sem sinal"},
            headers=auth_headers(user.id),
        )

        assert response.status_code == 422

    asyncio.run(scenario())


def test_create_phone_number_duplicate_conflicts() -> None:
    async def scenario() -> None:
        user = await create_user(email="dup@example.com")
        headers = auth_headers(user.id)

        first = await request(
            "POST", "/api/v1/numbers", json=PHONE_PAYLOAD, headers=headers
        )
        second = await request(
            "POST", "/api/v1/numbers", json=PHONE_PAYLOAD, headers=headers
        )

        assert first.status_code == 201
        assert second.status_code == 409

    asyncio.run(scenario())


def test_list_phone_numbers_scoped_to_owner() -> None:
    async def scenario() -> None:
        owner = await create_user(email="owner@example.com")
        other = await create_user(email="other@example.com")

        await request(
            "POST",
            "/api/v1/numbers",
            json=PHONE_PAYLOAD,
            headers=auth_headers(owner.id),
        )
        await request(
            "POST",
            "/api/v1/numbers",
            json={"phone_number": "+5585988888888", "name": "Other"},
            headers=auth_headers(other.id),
        )

        response = await request(
            "GET", "/api/v1/numbers", headers=auth_headers(owner.id)
        )

        assert response.status_code == 200
        numbers = response.json()
        assert len(numbers) == 1
        assert numbers[0]["phone_number"] == PHONE_PAYLOAD["phone_number"]

    asyncio.run(scenario())


def test_get_phone_number_not_found() -> None:
    async def scenario() -> None:
        user = await create_user(email="getnf@example.com")

        response = await request(
            "GET", "/api/v1/numbers/999", headers=auth_headers(user.id)
        )

        assert response.status_code == 404

    asyncio.run(scenario())


def test_get_phone_number_owned_by_another_user_is_hidden() -> None:
    async def scenario() -> None:
        owner = await create_user(email="secret-owner@example.com")
        intruder = await create_user(email="intruder@example.com")

        created = await request(
            "POST",
            "/api/v1/numbers",
            json=PHONE_PAYLOAD,
            headers=auth_headers(owner.id),
        )
        phone_id = created.json()["id"]

        response = await request(
            "GET",
            f"/api/v1/numbers/{phone_id}",
            headers=auth_headers(intruder.id),
        )

        assert response.status_code == 404

    asyncio.run(scenario())


def test_update_phone_number() -> None:
    async def scenario() -> None:
        user = await create_user(email="update@example.com")
        headers = auth_headers(user.id)

        created = await request(
            "POST", "/api/v1/numbers", json=PHONE_PAYLOAD, headers=headers
        )
        phone_id = created.json()["id"]

        response = await request(
            "PUT",
            f"/api/v1/numbers/{phone_id}",
            json={"phone_number": PHONE_PAYLOAD["phone_number"], "name": "Novo nome"},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Novo nome"

    asyncio.run(scenario())


def test_update_phone_number_conflicts_with_existing() -> None:
    async def scenario() -> None:
        user = await create_user(email="update-conflict@example.com")
        headers = auth_headers(user.id)

        await request("POST", "/api/v1/numbers", json=PHONE_PAYLOAD, headers=headers)
        second = await request(
            "POST",
            "/api/v1/numbers",
            json={"phone_number": "+5585988888888", "name": "Segundo"},
            headers=headers,
        )
        second_id = second.json()["id"]

        response = await request(
            "PUT",
            f"/api/v1/numbers/{second_id}",
            json={"phone_number": PHONE_PAYLOAD["phone_number"], "name": "Segundo"},
            headers=headers,
        )

        assert response.status_code == 409

    asyncio.run(scenario())


def test_delete_phone_number() -> None:
    async def scenario() -> None:
        user = await create_user(email="delete@example.com")
        headers = auth_headers(user.id)

        created = await request(
            "POST", "/api/v1/numbers", json=PHONE_PAYLOAD, headers=headers
        )
        phone_id = created.json()["id"]

        delete_response = await request(
            "DELETE", f"/api/v1/numbers/{phone_id}", headers=headers
        )
        get_response = await request(
            "GET", f"/api/v1/numbers/{phone_id}", headers=headers
        )

        assert delete_response.status_code == 204
        assert get_response.status_code == 404

    asyncio.run(scenario())
