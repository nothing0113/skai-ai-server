import asyncio

import httpx

from config import get_settings
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

    settings = get_settings()
    assert body["models"]["dense"]["configured"] == settings.dense_model_name
    assert body["models"]["sparse"]["configured"] == settings.sparse_model_name

    runtime = body["models"]["runtime"]
    assert runtime["loaded"] in {True, False}
    assert isinstance(runtime["fallback"], bool)


def test_default_device_is_auto():
    settings = get_settings()
    assert settings.device == "auto"
