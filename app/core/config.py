from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"

    database_url: str
    redis_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    ai_provider: str = "lmstudio"
    ai_base_url: str = "http://localhost:1234/v1"
    ai_api_key: str = "not-needed"
    ai_model: str = "qwen/qwen3.5-9b"
    ai_max_tokens: int = 1500


@lru_cache
def get_settings() -> Settings:
    return Settings()
