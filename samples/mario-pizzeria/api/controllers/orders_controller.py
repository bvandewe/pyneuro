from typing import List, Optional

from api.dtos import CreateOrderDto, OrderDto, UpdateOrderStatusDto
from application.commands import (
    CompleteOrderCommand,
    PlaceOrderCommand,
    StartCookingCommand,
)
from application.queries import (
    GetActiveOrdersQuery,
    GetOrderByIdQuery,
    GetOrdersByStatusQuery,
)
from classy_fastapi import get, post, put
from fastapi import HTTPException

from neuroglia.dependency_injection import ServiceProviderBase
from neuroglia.mapping import Mapper
from neuroglia.mediation import Mediator
from neuroglia.mvc import ControllerBase


class OrdersController(ControllerBase):
    """Mario's pizza order management endpoints"""

    def __init__(self, service_provider: ServiceProviderBase, mapper: Mapper, mediator: Mediator):
        super().__init__(service_provider, mapper, mediator)

    @get("/{order_id}", response_model=OrderDto, responses=ControllerBase.error_responses)
    async def get_order(self, order_id: str):
        """Get order details by ID"""
        query = GetOrderByIdQuery(order_id=order_id)
        result = await self.mediator.execute_async(query)
        return self.process(result)

    @get("/", response_model=List[OrderDto], responses=ControllerBase.error_responses)
    async def get_orders(self, status: Optional[str] = None):
        """Get orders, optionally filtered by status"""
        print(f"🔍 DEBUG: get_orders called with status={status}")

        # Let's test if we can resolve the services that the handler needs
        try:
            from domain.repositories import ICustomerRepository, IOrderRepository

            from neuroglia.mapping import Mapper

            order_repo = self.service_provider.get_service(IOrderRepository)
            customer_repo = self.service_provider.get_service(ICustomerRepository)
            mapper = self.service_provider.get_service(Mapper)

            print(f"🔍 DEBUG: IOrderRepository resolved: {order_repo is not None} ({type(order_repo)})")
            print(f"🔍 DEBUG: ICustomerRepository resolved: {customer_repo is not None} ({type(customer_repo)})")
            print(f"🔍 DEBUG: Mapper resolved: {mapper is not None} ({type(mapper)})")

        except Exception as e:
            print(f"❌ DEBUG: Service resolution failed: {e}")

        if status:
            query = GetOrdersByStatusQuery(status=status)
        else:
            query = GetActiveOrdersQuery()

        print(f"🔍 DEBUG: About to execute query: {type(query)}")
        result = await self.mediator.execute_async(query)
        return self.process(result)

    @post("/", response_model=OrderDto, status_code=201, responses=ControllerBase.error_responses)
    async def place_order(self, request: CreateOrderDto):
        """Place a new pizza order"""
        command = self.mapper.map(request, PlaceOrderCommand)
        result = await self.mediator.execute_async(command)
        return self.process(result)

    @put("/{order_id}/cook", response_model=OrderDto, responses=ControllerBase.error_responses)
    async def start_cooking(self, order_id: str):
        """Start cooking an order"""
        command = StartCookingCommand(order_id=order_id)
        result = await self.mediator.execute_async(command)
        return self.process(result)

    @put("/{order_id}/ready", response_model=OrderDto, responses=ControllerBase.error_responses)
    async def complete_order(self, order_id: str):
        """Mark order as ready for pickup/delivery"""
        command = CompleteOrderCommand(order_id=order_id)
        result = await self.mediator.execute_async(command)
        return self.process(result)

    @put("/{order_id}/status", response_model=OrderDto, responses=ControllerBase.error_responses)
    async def update_order_status(self, order_id: str, request: UpdateOrderStatusDto):
        """Update order status (general endpoint)"""
        # Route to appropriate command based on status
        if request.status.lower() == "cooking":
            command = StartCookingCommand(order_id=order_id)
        elif request.status.lower() == "ready":
            command = CompleteOrderCommand(order_id=order_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported status transition: {request.status}")

        result = await self.mediator.execute_async(command)
        return self.process(result)
