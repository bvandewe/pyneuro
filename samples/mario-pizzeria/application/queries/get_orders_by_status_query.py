"""Get Orders By Status Query and Handler for Mario's Pizzeria"""

from dataclasses import dataclass
from typing import List

from neuroglia.mediation import Query, QueryHandler
from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper

from api.dtos import OrderDto
from domain.entities import OrderStatus
from domain.repositories import IOrderRepository


@dataclass
class GetOrdersByStatusQuery(Query[OperationResult[List[OrderDto]]]):
    """Query to get orders by status"""

    status: str


class GetOrdersByStatusQueryHandler(
    QueryHandler[GetOrdersByStatusQuery, OperationResult[List[OrderDto]]]
):
    """Handler for getting orders by status"""

    def __init__(self, order_repository: IOrderRepository, mapper: Mapper):
        self.order_repository = order_repository
        self.mapper = mapper

    async def handle_async(
        self, request: GetOrdersByStatusQuery
    ) -> OperationResult[List[OrderDto]]:
        try:
            status = OrderStatus(request.status.lower())
            orders = await self.order_repository.get_orders_by_status_async(status)
            order_dtos = [self.mapper.map(order, OrderDto) for order in orders]
            return self.ok(order_dtos)

        except ValueError as e:
            return self.bad_request(f"Invalid status: {request.status}")
        except Exception as e:
            return self.bad_request(f"Failed to get orders by status: {str(e)}")
