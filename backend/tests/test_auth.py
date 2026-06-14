import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_creates_user_and_returns_token(client: AsyncClient) -> None:
    payload = {
        "email": "alice@example.com",
        "password": "SecurePass1",
        "tenant_name": "Alice Corp",
    }
    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 86400
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["role"] == "user"
    assert "id" in data["user"]
    assert "tenant_id" in data["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {"email": "bob@example.com", "password": "SecurePass1"}
    # First registration
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    # Second registration with same email
    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_password_too_short_returns_422(client: AsyncClient) -> None:
    payload = {"email": "short@example.com", "password": "123"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_without_tenant_name_defaults(client: AsyncClient) -> None:
    payload = {"email": "carol@example.com", "password": "SecurePass1"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_login_with_valid_credentials_returns_token(client: AsyncClient) -> None:
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dave@example.com", "password": "SecurePass1"},
    )
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "dave@example.com"


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "eve@example.com", "password": "SecurePass1"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "eve@example.com", "password": "WrongPass1"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_login_with_nonexistent_email_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token_returns_user(client: AsyncClient) -> None:
    # Register
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "frank@example.com", "password": "SecurePass1"},
    )
    token = reg.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "frank@example.com"
    assert data["role"] == "user"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401
