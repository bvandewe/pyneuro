"""Get Kitchen Status Query and Handler for Mario's Pizzeria"""

from dataclasses import dataclass

from neuroglia.mediation import Query, QueryHandler
from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper

from api.dtos import KitchenStatusDto
from domain.repositories import IKitchenRepository


@dataclass
class GetKitchenStatusQuery(Query[OperationResult[KitchenStatusDto]]):
    """Query to get current kitchen status and capacity"""

    pass


class GetKitchenStatusQueryHandler(
    QueryHandler[GetKitchenStatusQuery, OperationResult[KitchenStatusDto]]
):
    """Handler for getting kitchen status"""

    def __init__(self, kitchen_repository: IKitchenRepository, mapper: Mapper):
        self.kitchen_repository = kitchen_repository
        self.mapper = mapper

    async def handle_async(
        self, request: GetKitchenStatusQuery
    ) -> OperationResult[KitchenStatusDto]:
        try:
            kitchen = await self.kitchen_repository.get_kitchen_state_async()
            kitchen_dto = self.mapper.map(kitchen, KitchenStatusDto)
            return self.ok(kitchen_dto)

        except Exception as e:
            return self.bad_request(f"Failed to get kitchen status: {str(e)}")
