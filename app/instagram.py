from __future__ import annotations
import httpx
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from .models import Media, PrivateOrNotFound

GRAPH_BASE = "https://graph.facebook.com/v19.0"

class InstagramClient:
    def __init__(self, ig_user_id: str, access_token: str):
        self.ig_user_id = ig_user_id
        self.access_token = access_token
        self._client = httpx.AsyncClient(timeout=30)

    async def aclose(self):
        await self._client.aclose()

    def _params(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        p = {"access_token": self.access_token}
        if extra:
            p.update(extra)
        return p

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=3))
    async def _get(self, url: str, params: Dict[str, Any]) -> httpx.Response:
        return await self._client.get(url, params=params)

    async def find_media_by_permalink(self, permalink: str) -> Media:
        url = f"{GRAPH_BASE}/{self.ig_user_id}/media"
        params = self._params({
            "fields": "id,media_type,permalink",
            "limit": 50,
        })
        # First page
        r = await self._get(url, params)
        if r.status_code == 400:
            raise PrivateOrNotFound(f"Graph error: {r.text}")
        r.raise_for_status()
        data = r.json()
        while True:
            for item in data.get("data", []):
                if item.get("permalink") == permalink:
                    return await self.get_media(item["id"])
            next_url = data.get("paging", {}).get("next")
            if not next_url:
                break
            r = await self._client.get(next_url)
            if r.status_code == 400:
                raise PrivateOrNotFound(f"Graph error: {r.text}")
            r.raise_for_status()
            data = r.json()
        raise PrivateOrNotFound("Media not found in your account or access denied")

    async def get_media(self, media_id: str) -> Media:
        url = f"{GRAPH_BASE}/{media_id}"
        params = self._params({
            "fields": "id,media_type,media_url,video_url,permalink",
        })
        r = await self._get(url, params)
        if r.status_code == 400:
            raise PrivateOrNotFound(f"Graph error: {r.text}")
        r.raise_for_status()
        return Media(**r.json())
