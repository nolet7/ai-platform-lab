from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Platform API"
    app_env: str = "development"

    app_host: str = "127.0.0.1"
    app_port: int = 8001

    # Phase 2O observability
    metrics_enabled: bool = False
    metrics_port: int = 9091

    keycloak_realm: str = "ai-platform"

    keycloak_issuer: str
    keycloak_jwks_url: str

    keycloak_audience: str = "ai-platform-api"
    keycloak_algorithm: str = "RS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
