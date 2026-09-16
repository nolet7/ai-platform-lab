from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Platform Gateway"
    app_env: str = "development"

    http_port: int = 8080

    mock_provider_enabled: bool = True

    redis_enabled: bool = True
    redis_url: str = "redis://127.0.0.1:16379/0"

    cache_ttl_seconds: int = 120
    rate_limit_per_minute: int = 20

    opa_enabled: bool = True
    opa_url: str = "http://127.0.0.1:18181"
    opa_timeout_seconds: float = 2.0

    circuit_breaker_failure_threshold: int = 3
    circuit_breaker_open_seconds: int = 120

    failure_injection_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
