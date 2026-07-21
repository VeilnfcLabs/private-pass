"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "VeilPass API"
    version: str = "0.1.0"
    debug: bool = False
    signing_key: str = ""  # Ed25519 private key (hex)
    verification_key: str = ""  # Ed25519 public key (hex)
    default_token_ttl: int = 86400  # 24 hours
    max_token_ttl: int = 2592000  # 30 days
    database_url: str = "postgresql+asyncpg://veilpass:veilpass@localhost:5432/veilpass"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit: int = 100  # requests per minute
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "https://veilpass.app",
    ]

    model_config = {"env_prefix": "VEILPASS_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
