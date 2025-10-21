"""Application settings and configuration"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    """Application configuration"""

    # Application
    app_name: str = "Mario's Pizzeria"
    app_version: str = "1.0.0"
    debug: bool = True

    # Session (for UI)
    session_secret_key: str = "change-me-in-production-please-use-strong-key-32-chars-min"
    session_max_age: int = 3600  # 1 hour

    # JWT (for API)
    jwt_secret_key: str = "change-me-in-production-please-use-strong-jwt-key-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # OAuth (optional - for future SSO)
    oauth_enabled: bool = False
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    oauth_authorization_url: str = ""
    oauth_token_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )


app_settings = ApplicationSettings()
