"""Complete Order Command and Handler for Mario's Pizzeria"""

from dataclasses import dataclass

from neuroglia.mediation import Command, CommandHandler
from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper

from api.dtos import OrderDto
from domain.repositories import IOrderRepository, IKitchenRepository


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
        mapper: Mapper,
    ):
        self.order_repository = order_repository
        self.kitchen_repository = kitchen_repository
        self.mapper = mapper

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
            kitchen.complete_order(order.id)

            # Save changes
            await self.order_repository.update_async(order)
            await self.kitchen_repository.update_kitchen_state_async(kitchen)

            # Map to DTO and return
            order_dto = self.mapper.map(order, OrderDto)
            return self.ok(order_dto)

        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.bad_request(f"Failed to complete order: {str(e)}")
