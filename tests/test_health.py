import asyncio

import httpx

from main import app


def test_health():
    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/health")

    res = asyncio.run(_run())
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["provider"] in {"local", "openrouter"}
    assert body["device"] in {"cpu", "cuda"}
