"""Start Cooking Command and Handler for Mario's Pizzeria"""

from dataclasses import dataclass

from api.dtos import OrderDto, PizzaDto
from domain.repositories import (
    ICustomerRepository,
    IKitchenRepository,
    IOrderRepository,
)

from neuroglia.core import OperationResult
from neuroglia.data.unit_of_work import IUnitOfWork
from neuroglia.mapping import Mapper
from neuroglia.mediation import Command, CommandHandler


@dataclass
class StartCookingCommand(Command[OperationResult[OrderDto]]):
    """Command to start cooking an order"""

    order_id: str


class StartCookingCommandHandler(CommandHandler[StartCookingCommand, OperationResult[OrderDto]]):
    """Handler for starting to cook an order"""

    def __init__(
        self,
        order_repository: IOrderRepository,
        kitchen_repository: IKitchenRepository,
        customer_repository: ICustomerRepository,
        mapper: Mapper,
        unit_of_work: IUnitOfWork,
    ):
        self.order_repository = order_repository
        self.kitchen_repository = kitchen_repository
        self.customer_repository = customer_repository
        self.mapper = mapper
        self.unit_of_work = unit_of_work

    async def handle_async(self, request: StartCookingCommand) -> OperationResult[OrderDto]:
        try:
            # Get order
            order = await self.order_repository.get_async(request.order_id)
            if not order:
                return self.not_found("Order", request.order_id)

            # Get kitchen state
            kitchen = await self.kitchen_repository.get_kitchen_state_async()

            # Check kitchen capacity
            if kitchen.is_at_capacity:
                return self.bad_request("Kitchen is at capacity")

            # Start cooking order
            order.start_cooking()
            kitchen.start_order(order.id)

            # Save changes
            await self.order_repository.update_async(order)
            await self.kitchen_repository.update_kitchen_state_async(kitchen)

            # Register order with Unit of Work for domain event dispatching
            from typing import cast

            from neuroglia.data.abstractions import AggregateRoot as NeuroAggregateRoot

            self.unit_of_work.register_aggregate(cast(NeuroAggregateRoot, order))

            # Get customer details for DTO
            customer = await self.customer_repository.get_async(order.customer_id)

            # Create OrderDto manually
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

        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.bad_request(f"Failed to start cooking: {str(e)}")
