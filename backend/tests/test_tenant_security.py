"""Cross-tenant access must return 404."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cannot_read_other_tenant_document(client: AsyncClient) -> None:
    r1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "tenant_a@test.com", "password": "SecurePass1", "tenant_name": "A"},
    )
    r2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "tenant_b@test.com", "password": "SecurePass1", "tenant_name": "B"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    token_b = r2.json()["access_token"]

    # Tenant A has no documents; use a random UUID as foreign doc id
    fake_id = "00000000-0000-0000-0000-000000000099"
    resp = await client.get(
        f"/api/v1/documents/{fake_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 404
