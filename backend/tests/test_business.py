import asyncio

from conftest import auth_headers, create_business, create_user, request

SIGNUP_PAYLOAD = {
    "name": "Barbearia do Zé",
    "business_type": "barbearia",
    "contact_phone_number": "+5585999999999",
    "plan": "starter",
}


def test_signup_does_not_require_auth() -> None:
    response = asyncio.run(request("POST", "/api/v1/businesses/signup", json=SIGNUP_PAYLOAD))

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == SIGNUP_PAYLOAD["name"]
    assert body["status"] == "pending_setup"
    assert body["evolution_instance_name"] is None


def test_list_businesses_requires_admin() -> None:
    async def scenario() -> None:
        user = await create_user(email="not-admin@example.com", is_admin=False)

        response = await request(
            "GET", "/api/v1/businesses", headers=auth_headers(user.id)
        )
        assert response.status_code == 403

    asyncio.run(scenario())


def test_list_businesses_as_admin() -> None:
    async def scenario() -> None:
        admin = await create_user(email="admin@example.com", is_admin=True)
        await create_business(evolution_instance_name="biz-1", status="pending_setup")

        response = await request(
            "GET", "/api/v1/businesses", headers=auth_headers(admin.id)
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    asyncio.run(scenario())


def test_activate_requires_admin() -> None:
    async def scenario() -> None:
        user = await create_user(email="not-admin2@example.com", is_admin=False)
        business = await create_business(
            evolution_instance_name="pending-biz", status="pending_setup"
        )

        response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/activate",
            json={"evolution_instance_name": "pending-biz"},
            headers=auth_headers(user.id),
        )
        assert response.status_code == 403

    asyncio.run(scenario())


def test_activate_sets_instance_and_status() -> None:
    async def scenario() -> None:
        admin = await create_user(email="admin2@example.com", is_admin=True)
        signup = await request(
            "POST", "/api/v1/businesses/signup", json=SIGNUP_PAYLOAD
        )
        business_id = signup.json()["id"]

        response = await request(
            "POST",
            f"/api/v1/businesses/{business_id}/activate",
            json={"evolution_instance_name": "barbearia-do-ze"},
            headers=auth_headers(admin.id),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "active"
        assert body["evolution_instance_name"] == "barbearia-do-ze"

    asyncio.run(scenario())


def test_set_visibility_by_owner() -> None:
    async def scenario() -> None:
        owner = await create_user(email="visibility-owner@example.com")
        business = await create_business(
            evolution_instance_name="biz-visibility-owner", user_id=owner.id
        )

        response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/visibility",
            json={"visibility": "private"},
            headers=auth_headers(owner.id),
        )
        assert response.status_code == 200
        assert response.json()["visibility"] == "private"

    asyncio.run(scenario())


def test_set_visibility_by_admin() -> None:
    async def scenario() -> None:
        admin = await create_user(email="visibility-admin@example.com", is_admin=True)
        business = await create_business(evolution_instance_name="biz-visibility-admin")

        response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/visibility",
            json={"visibility": "private"},
            headers=auth_headers(admin.id),
        )
        assert response.status_code == 200

    asyncio.run(scenario())


def test_set_visibility_rejects_other_user() -> None:
    async def scenario() -> None:
        owner = await create_user(email="visibility-real-owner@example.com")
        intruder = await create_user(email="visibility-intruder@example.com")
        business = await create_business(
            evolution_instance_name="biz-visibility-guard", user_id=owner.id
        )

        response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/visibility",
            json={"visibility": "private"},
            headers=auth_headers(intruder.id),
        )
        assert response.status_code == 403

    asyncio.run(scenario())


def test_set_visibility_rejects_invalid_value() -> None:
    async def scenario() -> None:
        owner = await create_user(email="visibility-invalid@example.com")
        business = await create_business(
            evolution_instance_name="biz-visibility-invalid", user_id=owner.id
        )

        response = await request(
            "POST",
            f"/api/v1/businesses/{business.id}/visibility",
            json={"visibility": "invisible"},
            headers=auth_headers(owner.id),
        )
        assert response.status_code == 422

    asyncio.run(scenario())


def test_list_mine_scoped_to_current_user() -> None:
    async def scenario() -> None:
        owner = await create_user(email="mine-owner@example.com")
        other = await create_user(email="mine-other@example.com")
        await create_business(evolution_instance_name="biz-mine-a", user_id=owner.id)
        await create_business(evolution_instance_name="biz-mine-b", user_id=other.id)

        response = await request(
            "GET", "/api/v1/businesses/mine", headers=auth_headers(owner.id)
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["evolution_instance_name"] == "biz-mine-a"

    asyncio.run(scenario())


def test_activate_missing_business_returns_404() -> None:
    async def scenario() -> None:
        admin = await create_user(email="admin3@example.com", is_admin=True)

        response = await request(
            "POST",
            "/api/v1/businesses/999/activate",
            json={"evolution_instance_name": "whatever"},
            headers=auth_headers(admin.id),
        )
        assert response.status_code == 404

    asyncio.run(scenario())
