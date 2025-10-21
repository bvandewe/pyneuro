"""UI authentication endpoints (sessions)"""

import logging
from typing import Optional

from application.services.auth_service import AuthService
from classy_fastapi.decorators import get, post
from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from neuroglia.dependency_injection import ServiceProviderBase
from neuroglia.mapping.mapper import Mapper
from neuroglia.mediation.mediator import Mediator
from neuroglia.mvc.controller_base import ControllerBase

log = logging.getLogger(__name__)


class UIAuthController(ControllerBase):
    """UI authentication controller - session cookies"""

    def __init__(self, service_provider: ServiceProviderBase, mapper: Mapper, mediator: Mediator):
        # Store DI services first
        from neuroglia.serialization.json import JsonSerializer

        self.service_provider = service_provider
        self.mapper = mapper
        self.mediator = mediator
        self.json_serializer = service_provider.get_required_service(JsonSerializer)
        self.name = "Auth"

        # Initialize auth service
        self.auth_service = AuthService()

        # Call Routable.__init__ directly with /auth prefix
        from classy_fastapi import Routable

        from neuroglia.mvc.controller_base import generate_unique_id_function

        Routable.__init__(
            self,
            prefix="/auth",  # Auth routes prefix
            tags=["UI Auth"],
            generate_unique_id_function=generate_unique_id_function,
        )

    @get("/login", response_class=HTMLResponse)
    async def login_page(self, request: Request) -> HTMLResponse:
        """Render login page"""
        from application.settings import app_settings

        return request.app.state.templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "title": "Login", "app_version": app_settings.app_version},
        )

    @post("/login")
    async def login(
        self,
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        next_url: Optional[str] = Form(None),
    ) -> RedirectResponse:
        """Process login form and create session"""
        user = await self.auth_service.authenticate_user(username, password)

        if not user:
            # Re-render login with error
            from application.settings import app_settings

            return request.app.state.templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "title": "Login",
                    "error": "Invalid username or password",
                    "app_version": app_settings.app_version,
                },
                status_code=401,
            )

        # Create session
        request.session["user_id"] = user["id"]
        request.session["username"] = user["username"]
        request.session["authenticated"] = True

        log.info(f"User {username} logged in successfully")
        return RedirectResponse(url=next_url or "/", status_code=303)

    @get("/logout")
    async def logout(self, request: Request) -> RedirectResponse:
        """Clear session and redirect to home"""
        username = request.session.get("username", "Unknown")
        request.session.clear()
        log.info(f"User {username} logged out")
        return RedirectResponse(url="/", status_code=303)
