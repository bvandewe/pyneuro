"""Start Cooking Command and Handler for Mario's Pizzeria"""

from dataclasses import dataclass

from neuroglia.mediation import Command, CommandHandler
from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper

from api.dtos import OrderDto
from domain.repositories import IOrderRepository, IKitchenRepository


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
        mapper: Mapper,
    ):
        self.order_repository = order_repository
        self.kitchen_repository = kitchen_repository
        self.mapper = mapper

    async def handle_async(self, request: StartCookingCommand) -> OperationResult[OrderDto]:
        try:
            # Get order
            order = await self.order_repository.get_async(request.order_id)
            if not order:
                return self.not_found("Order", request.order_id)

            # Get kitchen state
            kitchen = await self.kitchen_repository.get_kitchen_state_async()

            # Check kitchen capacity
            if kitchen.is_busy:
                return self.bad_request("Kitchen is at capacity")

            # Start cooking order
            order.start_cooking()
            kitchen.start_cooking_order(order.id)

            # Save changes
            await self.order_repository.update_async(order)
            await self.kitchen_repository.update_kitchen_state_async(kitchen)

            # Map to DTO and return
            order_dto = self.mapper.map(order, OrderDto)
            return self.ok(order_dto)

        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.bad_request(f"Failed to start cooking: {str(e)}")
