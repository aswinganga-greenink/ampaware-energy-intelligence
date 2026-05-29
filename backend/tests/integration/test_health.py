"""
tests/integration/test_health.py
==================================
Integration tests for health check endpoints.

These tests use the TestClient (no real DB/Redis connections needed
for the liveness endpoint; detailed health is tested for correct structure).
"""
from __future__ import annotations

import pytest


@pytest.mark.integration
class TestLivenessEndpoint:
    async def test_liveness_returns_200(self, async_client) -> None:
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_liveness_returns_correct_fields(self, async_client) -> None:
        response = await async_client.get("/api/v1/health")
        body = response.json()
        assert body["status"] == "ok"
        assert "app" in body
        assert "version" in body

    async def test_liveness_is_fast(self, async_client) -> None:
        """Liveness probe must respond in < 500ms (no I/O)."""
        import time
        start = time.perf_counter()
        await async_client.get("/api/v1/health")
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 500, f"Liveness took {elapsed:.0f}ms — too slow"

    async def test_response_has_request_id_header(self, async_client) -> None:
        response = await async_client.get("/api/v1/health")
        assert "x-request-id" in response.headers

    async def test_response_has_security_headers(self, async_client) -> None:
        response = await async_client.get("/api/v1/health")
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers
