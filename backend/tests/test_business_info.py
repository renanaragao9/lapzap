import asyncio

from conftest import auth_headers, create_business, create_business_info, create_user, request


def test_get_info_requires_auth() -> None:
    response = asyncio.run(request("GET", "/api/v1/businesses/1/info"))
    assert response.status_code == 401


def test_get_info_404_when_not_set() -> None:
    async def scenario() -> None:
        owner = await create_user(email="info-owner1@example.com")
        business = await create_business(
            evolution_instance_name="info-biz-1", user_id=owner.id
        )

        response = await request(
            "GET",
            f"/api/v1/businesses/{business.id}/info",
            headers=auth_headers(owner.id),
        )
        assert response.status_code == 404

    asyncio.run(scenario())


def test_owner_creates_and_reads_info() -> None:
    async def scenario() -> None:
        owner = await create_user(email="info-owner2@example.com")
        business = await create_business(
            evolution_instance_name="info-biz-2", user_id=owner.id
        )

        put_response = await request(
            "PUT",
            f"/api/v1/businesses/{business.id}/info",
            json={"content": "# Sobre nós\nAtendemos das 9h às 18h."},
            headers=auth_headers(owner.id),
        )
        assert put_response.status_code == 200
        assert put_response.json()["content"] == "# Sobre nós\nAtendemos das 9h às 18h."

        get_response = await request(
            "GET",
            f"/api/v1/businesses/{business.id}/info",
            headers=auth_headers(owner.id),
        )
        assert get_response.status_code == 200
        assert get_response.json()["business_id"] == business.id

    asyncio.run(scenario())


def test_set_info_upserts_instead_of_duplicating() -> None:
    async def scenario() -> None:
        owner = await create_user(email="info-owner3@example.com")
        business = await create_business(
            evolution_instance_name="info-biz-3", user_id=owner.id
        )
        await create_business_info(business.id, content="versão 1")

        response = await request(
            "PUT",
            f"/api/v1/businesses/{business.id}/info",
            json={"content": "versão 2"},
            headers=auth_headers(owner.id),
        )
        assert response.status_code == 200
        assert response.json()["content"] == "versão 2"

    asyncio.run(scenario())


def test_set_info_forbidden_for_non_owner() -> None:
    async def scenario() -> None:
        owner = await create_user(email="info-owner4@example.com")
        stranger = await create_user(email="info-stranger@example.com")
        business = await create_business(
            evolution_instance_name="info-biz-4", user_id=owner.id
        )

        response = await request(
            "PUT",
            f"/api/v1/businesses/{business.id}/info",
            json={"content": "invasão"},
            headers=auth_headers(stranger.id),
        )
        assert response.status_code == 403

    asyncio.run(scenario())


def test_admin_can_manage_any_business_info() -> None:
    async def scenario() -> None:
        owner = await create_user(email="info-owner5@example.com")
        admin = await create_user(email="info-admin@example.com", is_admin=True)
        business = await create_business(
            evolution_instance_name="info-biz-5", user_id=owner.id
        )

        response = await request(
            "PUT",
            f"/api/v1/businesses/{business.id}/info",
            json={"content": "editado pelo admin"},
            headers=auth_headers(admin.id),
        )
        assert response.status_code == 200

    asyncio.run(scenario())


def test_delete_info() -> None:
    async def scenario() -> None:
        owner = await create_user(email="info-owner6@example.com")
        business = await create_business(
            evolution_instance_name="info-biz-6", user_id=owner.id
        )
        await create_business_info(business.id)

        delete_response = await request(
            "DELETE",
            f"/api/v1/businesses/{business.id}/info",
            headers=auth_headers(owner.id),
        )
        assert delete_response.status_code == 204

        get_response = await request(
            "GET",
            f"/api/v1/businesses/{business.id}/info",
            headers=auth_headers(owner.id),
        )
        assert get_response.status_code == 404

    asyncio.run(scenario())
