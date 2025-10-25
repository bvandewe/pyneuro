import logging
from typing import Optional

import httpx
import jwt  # `poetry add pyjwt`, not `poetry add jwt`
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException, Request
from fastapi.openapi.models import OAuthFlowClientCredentials
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED

log = logging.getLogger(__name__)


class Oauth2ClientCredentialsSettings(str):
    tokenUrl: str = ""

    def __repr__(self) -> str:
        return super().__repr__()


class Oauth2ClientCredentials(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str | None = None,
        scopes: dict | None = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(clientCredentials=OAuthFlowClientCredentials(tokenUrl=tokenUrl, scopes=scopes))
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        """Extracts the Bearer token from the Authorization Header"""
        authorization: str | None = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


def fix_public_key(key: str) -> str:
    """Fixes the format of a public key by adding headers and footers if missing.

    Supports both PEM public keys and X.509 certificates, extracting the public key
    from certificates when needed.

    Args:
        key: The public key string or certificate.

    Returns:
        The public key string with proper PEM formatting.
    """
    # Handle X.509 certificate format (from JWKS x5c)
    if "-----BEGIN CERTIFICATE-----" in key:
        try:
            # Parse the X.509 certificate and extract the public key
            cert_bytes = key.encode("utf-8")
            certificate = x509.load_pem_x509_certificate(cert_bytes)
            public_key = certificate.public_key()

            # Serialize the public key to PEM format
            pem_public_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return pem_public_key.decode("utf-8")
        except Exception as e:
            log.error(f"Failed to extract public key from X.509 certificate: {e}")
            # Fallback to using the certificate directly
            return key

    # Handle standard PEM public key format
    if "-----BEGIN PUBLIC KEY-----" not in key:
        key = f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"

    return key


async def get_public_key(jwt_authority: str) -> str | None:
    """Downloads the public key of a Keycloak Realm.

    Tries multiple endpoints in order:
    1. JWKS endpoint (standard): {jwt_authority}/protocol/openid-connect/certs
    2. Realm info endpoint (legacy): {jwt_authority} (returns JSON with .public_key)

    Args:
        jwt_authority (str): The base URL of the Keycloak Realm

    Returns:
        str: The public key encoded as a string, or None if not found
    """
    log.debug(f"Getting public key from {jwt_authority}")

    async with httpx.AsyncClient() as client:
        # Try JWKS endpoint first (standard approach)
        jwks_url = f"{jwt_authority}/protocol/openid-connect/certs"
        try:
            log.debug(f"Attempting to get JWKS from {jwks_url}")
            response = await client.get(jwks_url)
            response.raise_for_status()

            jwks_data = response.json()
            if "keys" in jwks_data and len(jwks_data["keys"]) > 0:
                # Get the first key (typically the active signing key)
                key_data = jwks_data["keys"][0]
                if "x5c" in key_data and len(key_data["x5c"]) > 0:
                    # Extract public key from x5c (X.509 certificate chain)
                    cert_data = key_data["x5c"][0]
                    public_key = f"-----BEGIN CERTIFICATE-----\n{cert_data}\n-----END CERTIFICATE-----"
                    log.debug(f"Successfully retrieved public key from JWKS endpoint")
                    return public_key
                elif "n" in key_data and "e" in key_data:
                    # RSA key components - would need additional processing
                    log.warning("JWKS contains RSA components (n,e) but x5c not available - falling back to realm endpoint")
                else:
                    log.warning("JWKS key format not recognized - falling back to realm endpoint")
        except Exception as e:
            log.warning(f"Failed to get key from JWKS endpoint {jwks_url}: {e}")

        # Fallback to legacy realm endpoint
        try:
            log.debug(f"Attempting to get public key from realm endpoint {jwt_authority}")
            response = await client.get(jwt_authority)
            response.raise_for_status()

            realm_data = response.json()
            if "public_key" in realm_data:
                key = realm_data["public_key"]
                log.debug(f"Successfully retrieved public key from realm endpoint")
                return key
            else:
                log.error(f"No public_key field found in realm response from {jwt_authority}")
                return None

        except httpx.ConnectError as e:
            log.error(f"Connection error while fetching public key from {jwt_authority}: {e}")
            return None
        except Exception as e:
            log.error(f"Error while fetching public key from {jwt_authority}: {e}")
            return None
