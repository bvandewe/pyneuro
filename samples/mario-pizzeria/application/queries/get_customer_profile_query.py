"""Query for retrieving customer profile"""

from dataclasses import dataclass
from typing import Optional

from api.dtos.profile_dtos import CustomerProfileDto
from domain.entities import Customer
from domain.repositories import ICustomerRepository, IOrderRepository

from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper
from neuroglia.mediation import Query, QueryHandler


@dataclass
class GetCustomerProfileQuery(Query[OperationResult[CustomerProfileDto]]):
    """
    Query to get customer profile.

    Supports lookup by either customer_id or user_id (Keycloak).
    Exactly one must be provided.
    """

    customer_id: Optional[str] = None
    user_id: Optional[str] = None


class GetCustomerProfileHandler(QueryHandler[GetCustomerProfileQuery, OperationResult[CustomerProfileDto]]):
    """Handler for customer profile queries"""

    def __init__(
        self,
        customer_repository: ICustomerRepository,
        order_repository: IOrderRepository,
        mapper: Mapper,
    ):
        self.customer_repository = customer_repository
        self.order_repository = order_repository
        self.mapper = mapper

    async def handle_async(self, request: GetCustomerProfileQuery) -> OperationResult[CustomerProfileDto]:
        """Handle profile retrieval by customer_id or user_id"""

        # Validate input - exactly one identifier must be provided
        if not request.customer_id and not request.user_id:
            return self.bad_request("Either customer_id or user_id must be provided")

        if request.customer_id and request.user_id:
            return self.bad_request("Cannot specify both customer_id and user_id")

        # Find customer by appropriate identifier
        customer: Optional[Customer] = None

        if request.customer_id:
            customer = await self.customer_repository.get_async(request.customer_id)
            if not customer:
                return self.not_found(Customer, request.customer_id)
        else:
            # user_id lookup
            customer = await self.customer_repository.get_by_user_id_async(request.user_id)
            if not customer:
                return self.bad_request(f"No customer profile found for user_id={request.user_id}")

        # Get order statistics - use customer-specific query instead of loading all orders
        customer_orders = await self.order_repository.get_by_customer_id_async(customer.id())

        # Calculate favorite pizza
        favorite_pizza = None
        if customer_orders:
            pizza_counts: dict[str, int] = {}
            for order in customer_orders:
                for item in order.state.order_items:
                    # Each OrderItem represents one pizza, so increment by 1
                    pizza_counts[item.name] = pizza_counts.get(item.name, 0) + 1
            if pizza_counts:
                favorite_pizza = max(pizza_counts, key=lambda name: pizza_counts[name])

        # Map to DTO (convert empty strings to None for validation)
        user_id = customer.state.user_id or ""
        profile_dto = CustomerProfileDto(
            id=customer.id(),
            user_id=user_id,
            name=customer.state.name or "",
            email=customer.state.email or "",
            phone=customer.state.phone if customer.state.phone else None,
            address=customer.state.address if customer.state.address else None,
            total_orders=len(customer_orders),
            favorite_pizza=favorite_pizza,
        )

        return self.ok(profile_dto)
