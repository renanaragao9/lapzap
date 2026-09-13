import asyncio

from conftest import auth_headers, create_business, create_user, request

GOOGLE_CALENDAR_PAYLOAD = {
    "name": "Agenda principal",
    "type": "google_calendar",
    "email": "agenda@empresa.com",
    "secret": "super-secreto-123",
}


def test_list_integrations_requires_auth() -> None:
    response = asyncio.run(request("GET", "/api/v1/businesses/1/integrations"))
    assert response.status_code == 401


def test_create_and_list_integration_hides_secret() -> None:
    async def scenario() -> None:
        owner = await create_user(email="int-owner1@example.com")
        business = await create_business(
            evolution_instance_name="int-biz-1", user_id=owner.id
        )
        headers = auth_headers(owner.id)

        create_response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/integrations",
            json=GOOGLE_CALENDAR_PAYLOAD,
            headers=headers,
        )
        assert create_response.status_code == 201
        body = create_response.json()
        assert body["name"] == "Agenda principal"
        assert body["type"] == "google_calendar"
        assert body["has_secret"] is True
        assert "secret" not in body
        assert "encrypted_secret" not in body

        list_response = await request(
            "GET", f"/api/v1/businesses/{business.id}/integrations", headers=headers
        )
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

    asyncio.run(scenario())


def test_secret_is_encrypted_at_rest() -> None:
    async def scenario() -> None:
        owner = await create_user(email="int-owner2@example.com")
        business = await create_business(
            evolution_instance_name="int-biz-2", user_id=owner.id
        )

        await request(
            "POST",
            f"/api/v1/businesses/{business.id}/integrations",
            json=GOOGLE_CALENDAR_PAYLOAD,
            headers=auth_headers(owner.id),
        )

        from conftest import session_factory
        from sqlalchemy import select

        from app.database.models.business_integration import BusinessIntegration
        from app.core.security import decrypt_secret

        async with session_factory() as session:
            integration = await session.scalar(
                select(BusinessIntegration).where(
                    BusinessIntegration.business_id == business.id
                )
            )
            assert integration is not None
            assert integration.encrypted_secret != "super-secreto-123"
            assert decrypt_secret(integration.encrypted_secret) == "super-secreto-123"

    asyncio.run(scenario())


def test_duplicate_name_conflicts() -> None:
    async def scenario() -> None:
        owner = await create_user(email="int-owner3@example.com")
        business = await create_business(
            evolution_instance_name="int-biz-3", user_id=owner.id
        )
        headers = auth_headers(owner.id)

        await request(
            "POST",
            f"/api/v1/businesses/{business.id}/integrations",
            json=GOOGLE_CALENDAR_PAYLOAD,
            headers=headers,
        )
        response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/integrations",
            json=GOOGLE_CALENDAR_PAYLOAD,
            headers=headers,
        )
        assert response.status_code == 409

    asyncio.run(scenario())


def test_create_forbidden_for_non_owner() -> None:
    async def scenario() -> None:
        owner = await create_user(email="int-owner4@example.com")
        stranger = await create_user(email="int-stranger@example.com")
        business = await create_business(
            evolution_instance_name="int-biz-4", user_id=owner.id
        )

        response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/integrations",
            json=GOOGLE_CALENDAR_PAYLOAD,
            headers=auth_headers(stranger.id),
        )
        assert response.status_code == 403

    asyncio.run(scenario())


def test_update_without_secret_keeps_existing_one() -> None:
    async def scenario() -> None:
        owner = await create_user(email="int-owner5@example.com")
        business = await create_business(
            evolution_instance_name="int-biz-5", user_id=owner.id
        )
        headers = auth_headers(owner.id)

        create_response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/integrations",
            json=GOOGLE_CALENDAR_PAYLOAD,
            headers=headers,
        )
        integration_id = create_response.json()["id"]

        update_response = await request(
            "PUT",
            f"/api/v1/businesses/{business.id}/integrations/{integration_id}",
            json={
                "name": "Agenda principal",
                "type": "google_calendar",
                "email": "novo-email@empresa.com",
            },
            headers=headers,
        )
        assert update_response.status_code == 200
        body = update_response.json()
        assert body["email"] == "novo-email@empresa.com"
        assert body["has_secret"] is True

        from conftest import session_factory

        from app.core.security import decrypt_secret
        from app.database.models.business_integration import BusinessIntegration

        async with session_factory() as session:
            integration = await session.get(BusinessIntegration, integration_id)
            assert decrypt_secret(integration.encrypted_secret) == "super-secreto-123"

    asyncio.run(scenario())


def test_delete_integration() -> None:
    async def scenario() -> None:
        owner = await create_user(email="int-owner6@example.com")
        business = await create_business(
            evolution_instance_name="int-biz-6", user_id=owner.id
        )
        headers = auth_headers(owner.id)

        create_response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/integrations",
            json=GOOGLE_CALENDAR_PAYLOAD,
            headers=headers,
        )
        integration_id = create_response.json()["id"]

        delete_response = await request(
            "DELETE",
            f"/api/v1/businesses/{business.id}/integrations/{integration_id}",
            headers=headers,
        )
        assert delete_response.status_code == 204

        list_response = await request(
            "GET", f"/api/v1/businesses/{business.id}/integrations", headers=headers
        )
        assert list_response.json() == []

    asyncio.run(scenario())
