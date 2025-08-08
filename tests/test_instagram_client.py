import httpx
import pytest
from app.instagram import InstagramClient

class _MockResp:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)

@pytest.mark.asyncio
async def test_find_media_by_permalink(monkeypatch):
    client = InstagramClient("123", "token")

    async def fake_get(url, params=None):
        if url.endswith("/123/media"):
            return _MockResp(200, {
                "data": [
                    {"id": "m1", "permalink": "https://www.instagram.com/p/ABC/", "media_type": "VIDEO"}
                ],
                "paging": {}
            })
        elif url.endswith("/m1"):
            return _MockResp(200, {
                "id": "m1",
                "media_type": "VIDEO",
                "video_url": "https://cdn.example.com/v.mp4",
                "permalink": "https://www.instagram.com/p/ABC/",
            })
        return _MockResp(404)

    monkeypatch.setattr(client, "_get", fake_get)
    media = await client.find_media_by_permalink("https://www.instagram.com/p/ABC/")
    assert media.video_url.endswith(".mp4")

    await client.aclose()
