"""Complete Order Command and Handler for Mario's Pizzeria"""

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
class CompleteOrderCommand(Command[OperationResult[OrderDto]]):
    """Command to mark an order as ready"""

    order_id: str


class CompleteOrderCommandHandler(CommandHandler[CompleteOrderCommand, OperationResult[OrderDto]]):
    """Handler for marking an order as ready"""

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

    async def handle_async(self, request: CompleteOrderCommand) -> OperationResult[OrderDto]:
        try:
            # Get order
            order = await self.order_repository.get_async(request.order_id)
            if not order:
                return self.not_found("Order", request.order_id)

            # Get kitchen state
            kitchen = await self.kitchen_repository.get_kitchen_state_async()

            # Mark order ready
            order.mark_ready()
            kitchen.complete_order(order.id())

            # Save changes
            await self.order_repository.update_async(order)
            await self.kitchen_repository.update_kitchen_state_async(kitchen)

            # Register order with Unit of Work for domain event dispatching
            self.unit_of_work.register_aggregate(order)

            # Get customer details for DTO
            customer = await self.customer_repository.get_async(order.state.customer_id)

            # Create OrderDto - Map OrderItems (value objects) to PizzaDtos
            pizza_dtos = [
                PizzaDto(
                    id=item.line_item_id,
                    name=item.name,
                    size=item.size.value,
                    toppings=list(item.toppings),
                    base_price=item.base_price,
                    total_price=item.total_price,
                )
                for item in order.state.order_items
            ]

            order_dto = OrderDto(
                id=order.id(),
                customer_name=customer.state.name if customer else "Unknown",
                customer_phone=customer.state.phone if customer else "Unknown",
                customer_address=customer.state.address if customer else "Unknown",
                pizzas=pizza_dtos,
                status=order.state.status.value,
                order_time=order.state.order_time,
                confirmed_time=getattr(order.state, "confirmed_time", None),
                cooking_started_time=getattr(order.state, "cooking_started_time", None),
                actual_ready_time=getattr(order.state, "actual_ready_time", None),
                estimated_ready_time=getattr(order.state, "estimated_ready_time", None),
                notes=getattr(order.state, "notes", None),
                total_amount=order.total_amount,
                pizza_count=order.pizza_count,
            )
            return self.ok(order_dto)

        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.bad_request(f"Failed to complete order: {str(e)}")
