import uuid

from httpx import AsyncClient


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


async def test_register_then_login_then_me(client: AsyncClient) -> None:
    email = _unique_email()
    password = "correcthorsebattery"

    register_response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == email

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


async def test_login_with_wrong_password_is_rejected(client: AsyncClient) -> None:
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "correcthorsebattery"}
    )

    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )
    assert response.status_code == 401


async def test_register_duplicate_email_is_rejected(client: AsyncClient) -> None:
    email = _unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "correcthorsebattery"}
    )

    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "another-password"}
    )
    assert response.status_code == 409


async def test_me_without_token_is_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
