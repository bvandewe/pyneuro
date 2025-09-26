"""Get Order By ID Query and Handler for Mario's Pizzeria"""

from dataclasses import dataclass

from api.dtos import OrderDto, PizzaDto
from domain.repositories import ICustomerRepository, IOrderRepository

from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper
from neuroglia.mediation import Query, QueryHandler


@dataclass
class GetOrderByIdQuery(Query[OperationResult[OrderDto]]):
    """Query to get an order by ID"""

    order_id: str


class GetOrderByIdQueryHandler(QueryHandler[GetOrderByIdQuery, OperationResult[OrderDto]]):
    """Handler for getting an order by ID"""

    def __init__(
        self,
        order_repository: IOrderRepository,
        customer_repository: ICustomerRepository,
        mapper: Mapper,
    ):
        self.order_repository = order_repository
        self.customer_repository = customer_repository
        self.mapper = mapper

    async def handle_async(self, request: GetOrderByIdQuery) -> OperationResult[OrderDto]:
        try:
            order = await self.order_repository.get_async(request.order_id)
            if not order:
                return self.not_found("Order", request.order_id)

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
            return self.ok(order_dto)

        except Exception as e:
            return self.bad_request(f"Failed to get order: {str(e)}")
