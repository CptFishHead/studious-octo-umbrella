from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Set
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from .models import FileTooLarge

_SHORTCODE_RE = re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel)/([A-Za-z0-9_-]+)/?")

def normalize_instagram_url(url: str) -> str:
    url = url.strip()
    url = re.sub(r"[?#].*$", "", url)
    url = re.sub(r"^http://", "https://", url)
    url = re.sub(r"^https://instagram.com/", "https://www.instagram.com/", url)
    if not url.endswith('/'):
        url += '/'
    return url

def extract_shortcode(url: str) -> str:
    m = _SHORTCODE_RE.match(url)
    if not m:
        raise ValueError("Unsupported Instagram URL. Use https://www.instagram.com/p/<code>/ or /reel/<code>/")
    return m.group(1)

def is_allowed(user_id: int, allowed: Optional[Set[int]]) -> bool:
    if allowed is None:
        return True
    return user_id in allowed

def bytes_to_mb(n: int) -> float:
    return n / (1024 * 1024)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=3))
async def _head(client: httpx.AsyncClient, url: str) -> httpx.Response:
    return await client.head(url, follow_redirects=True, timeout=30)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=3))
async def _get_stream(client: httpx.AsyncClient, url: str) -> httpx.Response:
    return await client.get(url, follow_redirects=True, timeout=None)

async def download_file(url: str, max_bytes: int) -> Path:
    tmp = Path("/tmp/ig_video.mp4")
    async with httpx.AsyncClient() as client:
        head = await _head(client, url)
        size_hdr = head.headers.get('Content-Length')
        if size_hdr is not None:
            size = int(size_hdr)
            if size > max_bytes:
                raise FileTooLarge(size_mb=bytes_to_mb(size), limit_mb=bytes_to_mb(max_bytes))
        r = await _get_stream(client, url)
        r.raise_for_status()
        with tmp.open('wb') as f:
            async for chunk in r.aiter_bytes(chunk_size=1024 * 512):
                f.write(chunk)
                if f.tell() > max_bytes:
                    f.close()
                    tmp.unlink(missing_ok=True)
                    raise FileTooLarge(bytes_to_mb(f.tell()), bytes_to_mb(max_bytes))
    return tmp
