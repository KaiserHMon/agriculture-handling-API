from functools import lru_cache
from typing import Literal

from pydantic import (
    EmailStr,
    SecretStr,
    field_validator,
)
from pydantic.networks import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variables validation using Pydantic.
    """

    # Application Settings
    APP_NAME: str = "Agriculture Handling API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = False

    # Security
    SECRET_KEY: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("CORS_ORIGINS")
    def validate_cors_origins(self, v: list[str]) -> list[AnyHttpUrl]:
        """Validate and parse CORS origins."""
        parsed_origins = []
        for origin in v:
            if isinstance(origin, str):
                parsed_origin = AnyHttpUrl(origin)
                parsed_origins.append(parsed_origin)
        return parsed_origins

    # Database Configuration
    DB_HOST: str | None = None
    DB_PORT: int | None = None
    DB_USER: str | None = None
    DB_PASSWORD: SecretStr | None = None
    DB_NAME: str | None = None
    DB_ECHO: bool = False

    @property
    def database_url(self) -> str | None:
        """Construct database URL from components."""
        if not all([self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_NAME]):
            return None
        db_password = self.DB_PASSWORD.get_secret_value() if self.DB_PASSWORD else ""
        return f"mysql+aiomysql://{self.DB_USER}:{db_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Email Configuration
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: SecretStr | None = None
    MAIL_FROM: EmailStr | None = None
    MAIL_PORT: int | None = None
    MAIL_SERVER: str | None = None
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True

    # Redis Configuration
    REDIS_HOST: str | None = None
    REDIS_PORT: int | None = None
    REDIS_DB: int = 0
    REDIS_PASSWORD: SecretStr | None = None

    @property
    def redis_url(self) -> str | None:
        """Construct Redis URL from components."""
        if not all([self.REDIS_HOST, self.REDIS_PORT, self.REDIS_PASSWORD]):
            return None
        redis_password = self.REDIS_PASSWORD.get_secret_value() if self.REDIS_PASSWORD else ""
        return f"redis://:{redis_password}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # External Services
    GRAIN_PRICES_API_KEY: SecretStr | None = None
    WEATHER_API_KEY: SecretStr | None = None
    GOOGLE_CALENDAR_API_KEY: SecretStr | None = None

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # Optional Features
    ENABLE_WEBSOCKETS: bool = True
    ENABLE_DOCS: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    @field_validator("SECRET_KEY")
    def validate_secret_key(self, v: str) -> str:
        """Validate that the secret key is secure enough."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY should be at least 32 characters long")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
