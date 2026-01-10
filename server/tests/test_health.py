"""Tests for health endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test /health returns ok status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_ready_endpoint(client: AsyncClient):
    """Test /ready returns ready status."""
    response = await client.get("/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_openapi_docs(client: AsyncClient):
    """Test OpenAPI documentation is available."""
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_json(client: AsyncClient):
    """Test OpenAPI JSON schema is available."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "FoodInsight API"
    assert data["info"]["version"] == "1.0.0"
