from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/employee_eval"
    ai_provider: Literal["mock", "anthropic", "openai"] = "mock"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-terra"


settings = Settings()
