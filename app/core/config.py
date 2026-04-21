from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    # Valkey
    valkey_host: str = "localhost"
    valkey_port: int = 6379
    valkey_password: Optional[str] = None   # ← changed from str to Optional[str]
    valkey_db: int = 0

    # JWT
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # OpenRouter / Nemotron
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    nemotron_model: str = "nvidia/llama-3.1-nemotron-70b-instruct:free"

    # App
    app_name: str = "ShopMind AI"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()