"""Customer profile management API endpoints"""

from typing import Any

from api.dtos import OrderDto
from api.dtos.profile_dtos import CreateProfileDto, CustomerProfileDto, UpdateProfileDto
from api.oauth2_scheme import validate_token
from application.commands import (
    CreateCustomerProfileCommand,
    UpdateCustomerProfileCommand,
)
from application.queries import (
    GetCustomerProfileQuery,
    GetOrCreateCustomerProfileQuery,
    GetOrdersByCustomerQuery,
)
from classy_fastapi import get, post, put
from fastapi import Depends, HTTPException, status

from neuroglia.dependency_injection import ServiceProviderBase
from neuroglia.mapping import Mapper
from neuroglia.mediation import Mediator
from neuroglia.mvc import ControllerBase


class ProfileController(ControllerBase):
    """Customer profile management endpoints"""

    def __init__(self, service_provider: ServiceProviderBase, mapper: Mapper, mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)

    def _get_user_id_from_token(self, token: dict[str, Any]) -> str:
        """Extract user ID (sub claim) from validated JWT token"""
        if "sub" not in token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing 'sub' claim",
            )
        return token["sub"]

    @get("/me", response_model=CustomerProfileDto, responses=ControllerBase.error_responses)
    async def get_my_profile(
        self,
        token: dict = Depends(validate_token),
    ):
        """Get current user's profile (requires authentication)

        If no profile exists by user_id, checks if one exists by email and links it.
        Otherwise creates a new profile from token claims.
        """
        user_id = self._get_user_id_from_token(token)

        # Extract user info from token for potential profile creation
        token_email = token.get("email")
        token_name = token.get("name", token.get("preferred_username", "User"))

        # Use GetOrCreateCustomerProfileQuery to handle all scenarios
        query = GetOrCreateCustomerProfileQuery(user_id=user_id, email=token_email, name=token_name)

        result = await self.mediator.execute_async(query)
        return self.process(result)

    @get(
        "/{customer_id}",
        response_model=CustomerProfileDto,
        responses=ControllerBase.error_responses,
    )
    async def get_profile(self, customer_id: str):
        """Get customer profile by ID"""
        query = GetCustomerProfileQuery(customer_id=customer_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)

    @post(
        "/",
        response_model=CustomerProfileDto,
        status_code=201,
        responses=ControllerBase.error_responses,
    )
    async def create_profile(
        self,
        request: CreateProfileDto,
        token: dict = Depends(validate_token),
    ):
        """Create a new customer profile (requires authentication)"""
        user_id = self._get_user_id_from_token(token)

        command = CreateCustomerProfileCommand(
            user_id=user_id,
            name=request.name,
            email=request.email,
            phone=request.phone,
            address=request.address,
        )
        result = await self.mediator.execute_async(command)
        return self.process(result)

    @put("/me", response_model=CustomerProfileDto, responses=ControllerBase.error_responses)
    async def update_my_profile(
        self,
        request: UpdateProfileDto,
        token: dict = Depends(validate_token),
    ):
        """Update current user's profile (requires authentication)"""
        user_id = self._get_user_id_from_token(token)

        # First get customer by user_id
        query = GetCustomerProfileQuery(user_id=user_id)
        profile_result = await self.mediator.execute_async(query)

        if not profile_result.is_success:
            return self.process(profile_result)

        profile = profile_result.data

        # Update profile
        command = UpdateCustomerProfileCommand(
            customer_id=profile.id,
            name=request.name,
            email=request.email,
            phone=request.phone,
            address=request.address,
        )
        result = await self.mediator.execute_async(command)
        return self.process(result)

    @get("/me/orders", response_model=list[OrderDto], responses=ControllerBase.error_responses)
    async def get_my_orders(
        self,
        token: dict = Depends(validate_token),
        limit: int = 50,
    ):
        """Get current user's order history (requires authentication)"""
        user_id = self._get_user_id_from_token(token)

        # First get customer by user_id
        profile_query = GetCustomerProfileQuery(user_id=user_id)
        profile_result = await self.mediator.execute_async(profile_query)

        if not profile_result.is_success:
            return self.process(profile_result)

        profile = profile_result.data

        # Get orders
        orders_query = GetOrdersByCustomerQuery(customer_id=profile.id, limit=limit)
        result = await self.mediator.execute_async(orders_query)
        return self.process(result)
