"""Get Order By ID Query and Handler for Mario's Pizzeria"""

from dataclasses import dataclass

from neuroglia.mediation import Query, QueryHandler
from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper

from api.dtos import OrderDto
from domain.repositories import IOrderRepository


@dataclass
class GetOrderByIdQuery(Query[OperationResult[OrderDto]]):
    """Query to get an order by ID"""

    order_id: str


class GetOrderByIdQueryHandler(QueryHandler[GetOrderByIdQuery, OperationResult[OrderDto]]):
    """Handler for getting an order by ID"""

    def __init__(self, order_repository: IOrderRepository, mapper: Mapper):
        self.order_repository = order_repository
        self.mapper = mapper

    async def handle_async(self, request: GetOrderByIdQuery) -> OperationResult[OrderDto]:
        try:
            order = await self.order_repository.get_async(request.order_id)
            if not order:
                return self.not_found("Order", request.order_id)

            order_dto = self.mapper.map(order, OrderDto)
            return self.ok(order_dto)

        except Exception as e:
            return self.bad_request(f"Failed to get order: {str(e)}")
