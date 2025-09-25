"""Get Active Orders Query and Handler for Mario's Pizzeria"""

from dataclasses import dataclass
from typing import List

from neuroglia.mediation import Query, QueryHandler
from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper

from api.dtos import OrderDto
from domain.repositories import IOrderRepository


@dataclass
class GetActiveOrdersQuery(Query[OperationResult[List[OrderDto]]]):
    """Query to get all active orders (not delivered or cancelled)"""

    pass


class GetActiveOrdersQueryHandler(
    QueryHandler[GetActiveOrdersQuery, OperationResult[List[OrderDto]]]
):
    """Handler for getting active orders"""

    def __init__(self, order_repository: IOrderRepository, mapper: Mapper):
        self.order_repository = order_repository
        self.mapper = mapper

    async def handle_async(self, request: GetActiveOrdersQuery) -> OperationResult[List[OrderDto]]:
        try:
            # Get all active orders (not delivered or cancelled)
            orders = await self.order_repository.get_active_orders_async()
            order_dtos = [self.mapper.map(order, OrderDto) for order in orders]
            return self.ok(order_dtos)

        except Exception as e:
            return self.bad_request(f"Failed to get active orders: {str(e)}")
