"""Application settings and configuration"""

from typing import Optional

from pydantic import computed_field
from pydantic_settings import SettingsConfigDict

from neuroglia.observability.settings import ApplicationSettingsWithObservability


class MarioPizzeriaApplicationSettings(ApplicationSettingsWithObservability):
    """Application configuration for Mario's Pizzeria with integrated observability

    Key URL Concepts:
    - Internal URLs (keycloak_*): Used by backend services running in Docker network
    - External URLs (swagger_ui_*): Used by browser/Swagger UI for OAuth2 flows

    Observability Features:
    - Comprehensive three pillars: metrics, tracing, logging
    - Standard endpoints: /health, /ready, /metrics
    - Health checks for MongoDB and Keycloak dependencies
    """

    # Application Identity (used by observability)
    service_name: str = "mario-pizzeria"
    service_version: str = "1.0.0"
    deployment_environment: str = "development"

    # Application Configuration
    app_name: str = "Mario's Pizzeria"
    debug: bool = True
    log_level: str = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    local_dev: bool = True  # True = development mode with localhost URLs for browser
    app_url: str = "http://localhost:8080"  # External URL where the app is accessible (Docker port mapping)

    # Session (for UI app)
    session_secret_key: str = "change-me-in-production-please-use-strong-key-32-chars-min"
    session_max_age: int = 3600  # 1 hour

    # Keycloak Configuration (Internal Docker network URLs - used by backend)
    keycloak_server_url: str = "http://keycloak:8080"  # Internal Docker network
    keycloak_realm: str = "mario-pizzeria"
    keycloak_client_id: str = "mario-app"
    keycloak_client_secret: str = "mario-secret-123"

    # JWT Validation (Backend token validation)
    jwt_signing_key: str = ""  # RSA public key - auto-discovered from Keycloak if empty
    jwt_audience: str = "mario-app"  # Expected audience claim in JWT (must match client_id)
    required_scope: str = "openid profile email"  # Required OAuth2 scopes

    # OAuth2 Scheme Type
    oauth2_scheme: Optional[str] = "authorization_code"  # "client_credentials" or "authorization_code"

    # CloudEvent Publishing Configuration (override base class defaults)
    cloud_event_sink: str = "http://localhost:8080/events"  # Where to publish CloudEvents
    cloud_event_source: str = "https://mario-pizzeria.com"  # Source identifier for events
    cloud_event_type_prefix: str = "com.mario-pizzeria"  # Prefix for event types
    cloud_event_retry_attempts: int = 5  # Number of retry attempts
    cloud_event_retry_delay: float = 1.0  # Delay between retries (seconds)

    # Swagger UI OAuth Configuration (External URLs - used by browser)
    swagger_ui_client_id: str = "mario-app"  # Must match keycloak_client_id
    swagger_ui_client_secret: str = ""  # Leave empty for public clients

    # Observability Configuration (Three Pillars)
    observability_enabled: bool = True
    observability_metrics_enabled: bool = True
    observability_tracing_enabled: bool = True
    observability_logging_enabled: bool = False  # Disable for local development (as its very resource intensive)

    # Standard Endpoints
    observability_health_endpoint: bool = True
    observability_metrics_endpoint: bool = True
    observability_ready_endpoint: bool = True

    # Health Check Dependencies
    observability_health_checks: list[str] = ["mongodb", "keycloak"]

    # OpenTelemetry Configuration
    otel_endpoint: str = "http://otel-collector:4317"  # Docker network endpoint
    otel_console_export: bool = False  # Enable for debugging

    # Computed Fields - Auto-generate URLs from base configuration
    @computed_field
    def jwt_authority(self) -> str:
        """Internal Keycloak authority URL (for backend token validation)"""
        return f"{self.keycloak_server_url}/realms/{self.keycloak_realm}"

    @computed_field
    def jwt_authorization_url(self) -> str:
        """Internal OAuth2 authorization URL"""
        return f"{self.jwt_authority}/protocol/openid-connect/auth"

    @computed_field
    def jwt_token_url(self) -> str:
        """Internal OAuth2 token URL"""
        return f"{self.jwt_authority}/protocol/openid-connect/token"

    @computed_field
    def swagger_ui_jwt_authority(self) -> str:
        """External Keycloak authority URL (for browser/Swagger UI)"""
        if self.local_dev:
            # Development: Browser connects to localhost:8090 (Keycloak Docker port mapping)
            return f"http://localhost:8090/realms/{self.keycloak_realm}"
        else:
            # Production: Browser connects to public Keycloak URL
            return f"{self.keycloak_server_url}/realms/{self.keycloak_realm}"

    @computed_field
    def swagger_ui_authorization_url(self) -> str:
        """External OAuth2 authorization URL (for browser)"""
        return f"{self.swagger_ui_jwt_authority}/protocol/openid-connect/auth"

    @computed_field
    def swagger_ui_token_url(self) -> str:
        """External OAuth2 token URL (for browser)"""
        return f"{self.swagger_ui_jwt_authority}/protocol/openid-connect/token"

    @computed_field
    def app_version(self) -> str:
        """Application version (alias for service_version for backward compatibility)"""
        return self.service_version

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )


app_settings = MarioPizzeriaApplicationSettings()
