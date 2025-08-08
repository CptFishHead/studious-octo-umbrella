from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Literal

class Media(BaseModel):
    id: str
    media_type: Literal['IMAGE', 'VIDEO', 'REEL', 'CAROUSEL_ALBUM']
    media_url: Optional[str] = None
    video_url: Optional[str] = None
    permalink: Optional[str] = None

class OEmbed(BaseModel):
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    html: Optional[str] = None
    thumbnail_url: Optional[str] = None
    title: Optional[str] = None

class NotVideo(Exception):
    pass

class PrivateOrNotFound(Exception):
    pass

class FileTooLarge(Exception):
    def __init__(self, size_mb: float, limit_mb: float):
        super().__init__(f"File size {size_mb:.2f}MB exceeds limit {limit_mb:.2f}MB")
        self.size_mb = size_mb
        self.limit_mb = limit_mb

class ForbiddenUser(Exception):
    pass
