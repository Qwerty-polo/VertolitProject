from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    database_url: str
    test_database_url: str
    redis_url: str

    redis_socket_connect_timeout_seconds: float = 1.0
    redis_socket_timeout_seconds: float = 1.0

    timezone: str = "Europe/Kyiv"

    business_start_hour: int = 10
    business_end_hour: int = 22

    availability_cache_ttl: int = 60

    minimum_advance_booking_hours: int = 2

    global_rate_limit: int = 30
    booking_rate_limit: int = 5
    rate_limit_window_seconds: int = 60

    max_booking_duration_hours: int = 12

    admin_password: str
    admin_session_ttl_seconds: int = 43200
    admin_cookie_secure: bool = False

    admin_login_rate_limit: int = 5
    admin_login_rate_limit_window_seconds: int = 600

    cors_origins: str = "http://localhost:3000"

    docs_enabled: bool = True

    sqlalchemy_echo: bool = False

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def fastapi_docs_enabled(self) -> bool:
        return (
            self.docs_enabled
            and not self.is_production
        )

    @model_validator(mode="after")
    def validate_production_settings(
        self,
    ) -> Self:
        if not self.is_production:
            return self

        if not self.admin_cookie_secure:
            raise ValueError(
                "ADMIN_COOKIE_SECURE must be true "
                "in production"
            )

        unsafe_origins = [
            origin
            for origin
            in self.allowed_cors_origins
            if (
                "localhost" in origin
                or "127.0.0.1" in origin
            )
        ]

        if unsafe_origins:
            raise ValueError(
                "localhost CORS origins are not "
                "allowed in production"
            )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()