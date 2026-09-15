from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    test_database_url: str
    redis_url: str

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()