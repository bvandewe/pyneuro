import logging
from typing import Any

import jwt
from application.settings import app_settings
from classy_fastapi.decorators import get
from fastapi import Request
from fastapi.responses import HTMLResponse

from neuroglia.dependency_injection import ServiceProviderBase
from neuroglia.mapping.mapper import Mapper
from neuroglia.mediation.mediator import Mediator
from neuroglia.mvc.controller_base import ControllerBase

log = logging.getLogger(__name__)


class HomeController(ControllerBase):
    """Controller for home UI views."""

    def __init__(self, service_provider: ServiceProviderBase, mapper: Mapper, mediator: Mediator):
        ControllerBase.__init__(self, service_provider, mapper, mediator)
        # Override class name to avoid path issues with classy_fastapi
        self.router.prefix = ""  # Reset the router prefix that gets auto-set to class name

    @get("/", response_class=HTMLResponse)
    async def home_view(self, request: Request) -> Any:
        """
        Render the home page.

        Authentication is handled client-side via JavaScript.
        The template includes elements that will be shown/hidden based on auth state.
        """
        access_token = request.session.get("access_token", None)
        token_payload = None
        if access_token:
            try:
                # Decode without verifying signature (for extracting claims only)
                token_payload = jwt.decode(access_token, options={"verify_signature": False})
                if not isinstance(token_payload, dict):
                    log.warning("Decoded access token is not a valid dictionary")
                    token_payload = None
            except Exception as e:
                log.warning(f"Failed to decode access token: {e}")

        try:
            username = token_payload.get("preferred_username", token_payload.get("username", "Guest")) if token_payload else "Guest"
            return request.app.state.templates.TemplateResponse(
                "home/index.html",
                {
                    "request": request,
                    "title": "Home",
                    "active_page": "home",
                    "app_version": app_settings.app_version,
                    "authenticated": token_payload is not None,
                    "username": username,
                },
            )

        except Exception as e:
            log.error(f"Unexpected error in comments_view: {str(e)}")
            raise
