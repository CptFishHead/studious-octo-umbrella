from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Set
import os

class Settings(BaseModel):
    TELEGRAM_BOT_TOKEN: str
    IG_USER_ID: str
    IG_ACCESS_TOKEN: str
    TELEGRAM_ALLOWED_USER_IDS: Optional[str] = None
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    MAX_FILE_MB: int = 45
    LOG_LEVEL: str = "INFO"

    @property
    def allowed_user_ids(self) -> Optional[Set[int]]:
        if not self.TELEGRAM_ALLOWED_USER_IDS:
            return None
        ids: Set[int] = set()
        for part in self.TELEGRAM_ALLOWED_USER_IDS.split(','):
            part = part.strip()
            if part:
                try:
                    ids.add(int(part))
                except ValueError:
                    continue
        return ids or None

def load_settings() -> Settings:
    from dotenv import load_dotenv
    load_dotenv(override=False)
    return Settings(
        TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        IG_USER_ID=os.getenv("IG_USER_ID", ""),
        IG_ACCESS_TOKEN=os.getenv("IG_ACCESS_TOKEN", ""),
        TELEGRAM_ALLOWED_USER_IDS=os.getenv("TELEGRAM_ALLOWED_USER_IDS"),
        TELEGRAM_WEBHOOK_URL=os.getenv("TELEGRAM_WEBHOOK_URL"),
        HOST=os.getenv("HOST", "0.0.0.0"),
        PORT=int(os.getenv("PORT", "8080")),
        MAX_FILE_MB=int(os.getenv("MAX_FILE_MB", "45")),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
    )
