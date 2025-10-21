"""Authentication service for both session and JWT"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from application.settings import app_settings
from passlib.context import CryptContext


class AuthService:
    """Handles authentication for both UI (sessions) and API (JWT)"""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Password hashing
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    # JWT Token Management (for API)
    def create_jwt_token(self, user_id: str, username: str, extra_claims: Optional[dict[str, Any]] = None) -> str:
        """Create a JWT access token for API authentication"""
        payload = {
            "sub": user_id,
            "username": username,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=app_settings.jwt_expiration_minutes),
            "iat": datetime.now(timezone.utc),
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, app_settings.jwt_secret_key, algorithm=app_settings.jwt_algorithm)

    def verify_jwt_token(self, token: str) -> Optional[dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token,
                app_settings.jwt_secret_key,
                algorithms=[app_settings.jwt_algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # User Authentication (placeholder - implement with real user repo)
    async def authenticate_user(self, username: str, password: str) -> Optional[dict[str, Any]]:
        """
        Authenticate a user with username/password.

        TODO: Replace with real user repository lookup
        """
        # Placeholder - in production, query user repository
        if username == "demo" and password == "demo123":
            return {
                "id": "demo-user-id",
                "username": "demo",
                "email": "demo@mariospizzeria.com",
                "role": "customer",
            }
        return None
