import asyncio

from conftest import auth_headers, create_user, request

NEW_USER_PAYLOAD = {
    "name": "Novo Usuário",
    "email": "novo@example.com",
    "password": "123456",
    "is_active": True,
    "is_admin": False,
}


def test_users_require_admin() -> None:
    async def scenario() -> None:
        regular = await create_user(email="regular@example.com")

        response = await request(
            "GET", "/api/v1/users", headers=auth_headers(regular.id)
        )

        assert response.status_code == 403

    asyncio.run(scenario())


def test_users_require_auth() -> None:
    response = asyncio.run(request("GET", "/api/v1/users"))
    assert response.status_code == 401


def test_admin_can_create_list_and_update_user() -> None:
    async def scenario() -> None:
        admin = await create_user(email="admin@example.com", is_admin=True)
        headers = auth_headers(admin.id)

        create_response = await request(
            "POST", "/api/v1/users", json=NEW_USER_PAYLOAD, headers=headers
        )
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["email"] == NEW_USER_PAYLOAD["email"]
        assert "password" not in created
        assert "password_hash" not in created

        list_response = await request("GET", "/api/v1/users", headers=headers)
        assert list_response.status_code == 200
        emails = [u["email"] for u in list_response.json()]
        assert NEW_USER_PAYLOAD["email"] in emails
        assert "admin@example.com" in emails

        update_response = await request(
            "PUT",
            f"/api/v1/users/{created['id']}",
            json={
                "name": "Usuário Editado",
                "email": NEW_USER_PAYLOAD["email"],
                "is_active": False,
                "is_admin": True,
            },
            headers=headers,
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Usuário Editado"
        assert updated["is_active"] is False
        assert updated["is_admin"] is True

    asyncio.run(scenario())


def test_create_user_rejects_duplicate_email() -> None:
    async def scenario() -> None:
        admin = await create_user(email="admin2@example.com", is_admin=True)
        headers = auth_headers(admin.id)

        first = await request(
            "POST", "/api/v1/users", json=NEW_USER_PAYLOAD, headers=headers
        )
        second = await request(
            "POST", "/api/v1/users", json=NEW_USER_PAYLOAD, headers=headers
        )

        assert first.status_code == 201
        assert second.status_code == 409

    asyncio.run(scenario())


def test_admin_cannot_delete_self() -> None:
    async def scenario() -> None:
        admin = await create_user(email="admin3@example.com", is_admin=True)
        headers = auth_headers(admin.id)

        response = await request(
            "DELETE", f"/api/v1/users/{admin.id}", headers=headers
        )

        assert response.status_code == 400

    asyncio.run(scenario())


def test_admin_cannot_delete_user_with_numbers() -> None:
    async def scenario() -> None:
        admin = await create_user(email="admin4@example.com", is_admin=True)
        other = await create_user(email="withnumber@example.com")
        headers = auth_headers(admin.id)

        await request(
            "POST",
            "/api/v1/numbers",
            json={"phone_number": "+5585999999999", "name": "Número"},
            headers=auth_headers(other.id),
        )

        response = await request(
            "DELETE", f"/api/v1/users/{other.id}", headers=headers
        )

        assert response.status_code == 409

    asyncio.run(scenario())


def test_admin_can_delete_user_without_numbers() -> None:
    async def scenario() -> None:
        admin = await create_user(email="admin5@example.com", is_admin=True)
        other = await create_user(email="removable@example.com")
        headers = auth_headers(admin.id)

        response = await request(
            "DELETE", f"/api/v1/users/{other.id}", headers=headers
        )

        assert response.status_code == 204

        get_response = await request(
            "GET", f"/api/v1/users/{other.id}", headers=headers
        )
        assert get_response.status_code == 404

    asyncio.run(scenario())
