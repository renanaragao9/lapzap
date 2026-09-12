import asyncio

from conftest import auth_headers, create_business, create_user, request


async def payload(business_id: int, phone_number: str = "+5585999999999") -> dict:
    return {"phone_number": phone_number, "name": "Renan", "business_id": business_id}


def test_create_phone_number() -> None:
    async def scenario() -> None:
        user = await create_user(email="create@example.com")
        business = await create_business(
            evolution_instance_name="biz-create", user_id=user.id
        )

        response = await request(
            "POST",
            "/api/v1/numbers",
            json=await payload(business.id),
            headers=auth_headers(user.id),
        )

        assert response.status_code == 201
        body = response.json()
        assert body["phone_number"] == "+5585999999999"
        assert body["is_active"] is True

    asyncio.run(scenario())


def test_create_phone_number_rejects_invalid_format() -> None:
    async def scenario() -> None:
        user = await create_user(email="invalid@example.com")
        business = await create_business(
            evolution_instance_name="biz-invalid", user_id=user.id
        )

        response = await request(
            "POST",
            "/api/v1/numbers",
            json={
                "phone_number": "5585999999999",
                "name": "Sem sinal",
                "business_id": business.id,
            },
            headers=auth_headers(user.id),
        )

        assert response.status_code == 422

    asyncio.run(scenario())


def test_create_phone_number_rejects_business_of_another_user() -> None:
    async def scenario() -> None:
        owner = await create_user(email="biz-owner@example.com")
        intruder = await create_user(email="biz-intruder@example.com")
        business = await create_business(
            evolution_instance_name="biz-not-yours", user_id=owner.id
        )

        response = await request(
            "POST",
            "/api/v1/numbers",
            json=await payload(business.id),
            headers=auth_headers(intruder.id),
        )

        assert response.status_code == 403

    asyncio.run(scenario())


def test_create_phone_number_duplicate_conflicts() -> None:
    async def scenario() -> None:
        user = await create_user(email="dup@example.com")
        business = await create_business(
            evolution_instance_name="biz-dup", user_id=user.id
        )
        headers = auth_headers(user.id)

        first = await request(
            "POST", "/api/v1/numbers", json=await payload(business.id), headers=headers
        )
        second = await request(
            "POST", "/api/v1/numbers", json=await payload(business.id), headers=headers
        )

        assert first.status_code == 201
        assert second.status_code == 409

    asyncio.run(scenario())


def test_same_number_allowed_on_different_businesses() -> None:
    # unique agora e por negocio, nao mais global - dois negocios podem ter
    # o mesmo numero de cliente autorizado
    async def scenario() -> None:
        user = await create_user(email="two-biz@example.com")
        biz_a = await create_business(evolution_instance_name="biz-a", user_id=user.id)
        biz_b = await create_business(evolution_instance_name="biz-b", user_id=user.id)
        headers = auth_headers(user.id)

        first = await request(
            "POST", "/api/v1/numbers", json=await payload(biz_a.id), headers=headers
        )
        second = await request(
            "POST", "/api/v1/numbers", json=await payload(biz_b.id), headers=headers
        )

        assert first.status_code == 201
        assert second.status_code == 201

    asyncio.run(scenario())


def test_list_phone_numbers_scoped_to_business() -> None:
    async def scenario() -> None:
        owner = await create_user(email="owner@example.com")
        other = await create_user(email="other@example.com")
        owner_business = await create_business(
            evolution_instance_name="biz-owner-list", user_id=owner.id
        )
        other_business = await create_business(
            evolution_instance_name="biz-other-list", user_id=other.id
        )

        await request(
            "POST",
            "/api/v1/numbers",
            json=await payload(owner_business.id),
            headers=auth_headers(owner.id),
        )
        await request(
            "POST",
            "/api/v1/numbers",
            json=await payload(other_business.id, "+5585988888888"),
            headers=auth_headers(other.id),
        )

        response = await request(
            "GET",
            "/api/v1/numbers",
            params={"business_id": owner_business.id},
            headers=auth_headers(owner.id),
        )

        assert response.status_code == 200
        numbers = response.json()
        assert len(numbers) == 1
        assert numbers[0]["phone_number"] == "+5585999999999"

    asyncio.run(scenario())


def test_list_phone_numbers_rejects_business_of_another_user() -> None:
    async def scenario() -> None:
        owner = await create_user(email="list-owner@example.com")
        intruder = await create_user(email="list-intruder@example.com")
        business = await create_business(
            evolution_instance_name="biz-list-guard", user_id=owner.id
        )

        response = await request(
            "GET",
            "/api/v1/numbers",
            params={"business_id": business.id},
            headers=auth_headers(intruder.id),
        )

        assert response.status_code == 403

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
        business = await create_business(
            evolution_instance_name="biz-secret", user_id=owner.id
        )

        created = await request(
            "POST",
            "/api/v1/numbers",
            json=await payload(business.id),
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
        business = await create_business(
            evolution_instance_name="biz-update", user_id=user.id
        )
        headers = auth_headers(user.id)

        created = await request(
            "POST", "/api/v1/numbers", json=await payload(business.id), headers=headers
        )
        phone_id = created.json()["id"]

        response = await request(
            "PUT",
            f"/api/v1/numbers/{phone_id}",
            json={
                "phone_number": "+5585999999999",
                "name": "Novo nome",
                "business_id": business.id,
            },
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Novo nome"

    asyncio.run(scenario())


def test_update_phone_number_conflicts_with_existing() -> None:
    async def scenario() -> None:
        user = await create_user(email="update-conflict@example.com")
        business = await create_business(
            evolution_instance_name="biz-update-conflict", user_id=user.id
        )
        headers = auth_headers(user.id)

        await request(
            "POST", "/api/v1/numbers", json=await payload(business.id), headers=headers
        )
        second = await request(
            "POST",
            "/api/v1/numbers",
            json=await payload(business.id, "+5585988888888"),
            headers=headers,
        )
        second_id = second.json()["id"]

        response = await request(
            "PUT",
            f"/api/v1/numbers/{second_id}",
            json={
                "phone_number": "+5585999999999",
                "name": "Segundo",
                "business_id": business.id,
            },
            headers=headers,
        )

        assert response.status_code == 409

    asyncio.run(scenario())


def test_delete_phone_number() -> None:
    async def scenario() -> None:
        user = await create_user(email="delete@example.com")
        business = await create_business(
            evolution_instance_name="biz-delete", user_id=user.id
        )
        headers = auth_headers(user.id)

        created = await request(
            "POST", "/api/v1/numbers", json=await payload(business.id), headers=headers
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
