"""Get Active Orders Query and Handler for Mario's Pizzeria"""

from dataclasses import dataclass
from typing import List

from api.dtos import OrderDto, PizzaDto
from domain.repositories import ICustomerRepository, IOrderRepository

from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper
from neuroglia.mediation import Query, QueryHandler


@dataclass
class GetActiveOrdersQuery(Query[OperationResult[List[OrderDto]]]):
    """Query to get all active orders (not delivered or cancelled)"""


class GetActiveOrdersQueryHandler(QueryHandler[GetActiveOrdersQuery, OperationResult[List[OrderDto]]]):
    """Handler for getting active orders"""

    def __init__(
        self,
        order_repository: IOrderRepository,
        customer_repository: ICustomerRepository,
        mapper: Mapper,
    ):
        self.order_repository = order_repository
        self.customer_repository = customer_repository
        self.mapper = mapper

    async def handle_async(self, request: GetActiveOrdersQuery) -> OperationResult[list[OrderDto]]:
        try:
            # Get all active orders (not delivered or cancelled)
            orders = await self.order_repository.get_active_orders_async()

            order_dtos = []
            for order in orders:
                # Get customer details
                customer = await self.customer_repository.get_async(order.customer_id)

                # Create OrderDto with customer information
                order_dto = OrderDto(
                    id=order.id,
                    customer_name=customer.name if customer else "Unknown",
                    customer_phone=customer.phone if customer else "Unknown",
                    customer_address=customer.address if customer else "Unknown",
                    pizzas=[self.mapper.map(pizza, PizzaDto) for pizza in order.pizzas],
                    status=order.status.value,
                    order_time=order.order_time,
                    confirmed_time=order.confirmed_time,
                    cooking_started_time=order.cooking_started_time,
                    actual_ready_time=order.actual_ready_time,
                    estimated_ready_time=order.estimated_ready_time,
                    notes=order.notes,
                    total_amount=order.total_amount,
                    pizza_count=order.pizza_count,
                )
                order_dtos.append(order_dto)

            return self.ok(order_dtos)

        except Exception as e:
            return self.bad_request(f"Failed to get active orders: {str(e)}")
