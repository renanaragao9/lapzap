import asyncio

from conftest import auth_headers, create_user, request


def test_login_success() -> None:
    async def scenario() -> None:
        await create_user(email="login@example.com", password="secret123")

        response = await request(
            "POST",
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "secret123"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]

    asyncio.run(scenario())


def test_login_wrong_password() -> None:
    async def scenario() -> None:
        await create_user(email="wrongpass@example.com", password="secret123")

        response = await request(
            "POST",
            "/api/v1/auth/login",
            json={"email": "wrongpass@example.com", "password": "invalid"},
        )

        assert response.status_code == 401

    asyncio.run(scenario())


def test_login_unknown_email() -> None:
    async def scenario() -> None:
        response = await request(
            "POST",
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "whatever"},
        )

        assert response.status_code == 401

    asyncio.run(scenario())


def test_login_inactive_user() -> None:
    async def scenario() -> None:
        await create_user(
            email="inactive@example.com",
            password="secret123",
            is_active=False,
        )

        response = await request(
            "POST",
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "secret123"},
        )

        assert response.status_code == 401

    asyncio.run(scenario())


def test_protected_route_rejects_invalid_token() -> None:
    async def scenario() -> None:
        response = await request(
            "GET",
            "/api/v1/numbers",
            headers={"Authorization": "Bearer not-a-real-token"},
        )

        assert response.status_code == 401

    asyncio.run(scenario())


def test_protected_route_requires_token() -> None:
    async def scenario() -> None:
        response = await request("GET", "/api/v1/numbers")

        assert response.status_code == 401

    asyncio.run(scenario())


def test_me_returns_current_user() -> None:
    async def scenario() -> None:
        user = await create_user(email="me@example.com", is_admin=True)

        response = await request(
            "GET",
            "/api/v1/auth/me",
            headers=auth_headers(user.id),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "me@example.com"
        assert body["is_admin"] is True
        assert "password" not in body
        assert "password_hash" not in body

    asyncio.run(scenario())
