"""Get Menu Query and Handler for Mario's Pizzeria"""

from dataclasses import dataclass
from typing import List

from neuroglia.mediation import Query, QueryHandler
from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper

from api.dtos import PizzaDto
from domain.repositories import IPizzaRepository


@dataclass
class GetMenuQuery(Query[OperationResult[List[PizzaDto]]]):
    """Query to get the complete pizza menu"""

    pass


class GetMenuQueryHandler(QueryHandler[GetMenuQuery, OperationResult[List[PizzaDto]]]):
    """Handler for getting the pizza menu"""

    def __init__(self, pizza_repository: IPizzaRepository, mapper: Mapper):
        self.pizza_repository = pizza_repository
        self.mapper = mapper

    async def handle_async(self, request: GetMenuQuery) -> OperationResult[List[PizzaDto]]:
        try:
            pizzas = await self.pizza_repository.get_available_pizzas_async()
            pizza_dtos = [self.mapper.map(pizza, PizzaDto) for pizza in pizzas]
            return self.ok(pizza_dtos)

        except Exception as e:
            return self.bad_request(f"Failed to get menu: {str(e)}")
