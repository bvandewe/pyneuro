"""Place Order Command and Handler for Mario's Pizzeria"""

from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal

from neuroglia.mediation import Command, CommandHandler
from neuroglia.core import OperationResult
from neuroglia.mapping import Mapper

from api.dtos import OrderDto, PizzaOrderItemDto
from domain.entities import Order, Pizza, PizzaSize, Customer
from domain.repositories import IOrderRepository, ICustomerRepository, IPizzaRepository


@dataclass
class PlaceOrderCommand(Command[OperationResult[OrderDto]]):
    """Command to place a new pizza order"""

    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    pizzas: List[PizzaOrderItemDto] = field(default_factory=list)
    payment_method: str = "cash"
    delivery_fee: Decimal = Decimal("0.00")
    notes: Optional[str] = None


class PlaceOrderCommandHandler(CommandHandler[PlaceOrderCommand, OperationResult[OrderDto]]):
    """Handler for placing new pizza orders"""

    def __init__(
        self,
        order_repository: IOrderRepository,
        customer_repository: ICustomerRepository,
        pizza_repository: IPizzaRepository,
        mapper: Mapper,
    ):
        self.order_repository = order_repository
        self.customer_repository = customer_repository
        self.pizza_repository = pizza_repository
        self.mapper = mapper

    async def handle_async(self, request: PlaceOrderCommand) -> OperationResult[OrderDto]:
        try:
            # Create order
            order = Order(
                customer_name=request.customer_name,
                customer_phone=request.customer_phone,
                customer_address=request.customer_address,
            )
            order.payment_method = request.payment_method
            order.delivery_fee = request.delivery_fee
            if request.notes:
                order.notes = request.notes

            # Add pizzas to order
            for pizza_item in request.pizzas:
                # Convert size string to enum
                size = PizzaSize(pizza_item.size.lower())

                # Create pizza (in real app, would fetch from menu)
                pizza = Pizza(
                    name=pizza_item.name,
                    size=size,
                    base_price=Decimal("15.99"),  # Base price from menu
                    toppings=pizza_item.toppings,
                    preparation_time_minutes=15,
                )
                order.add_pizza(pizza)

            # Validate order has pizzas
            if not order.pizzas:
                return self.bad_request("Order must contain at least one pizza")

            # Confirm order (raises domain event)
            order.confirm_order()

            # Save order
            saved_order = await self.order_repository.save_async(order)

            # Create or update customer
            await self._create_or_update_customer(request)

            # Map to DTO and return
            order_dto = self.mapper.map(saved_order, OrderDto)
            return self.created(order_dto)

        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.bad_request(f"Failed to place order: {str(e)}")

    async def _create_or_update_customer(self, request: PlaceOrderCommand) -> None:
        """Create or update customer record"""
        existing_customer = await self.customer_repository.get_by_phone_async(
            request.customer_phone
        )

        if not existing_customer:
            customer = Customer(
                name=request.customer_name,
                phone=request.customer_phone,
                address=request.customer_address,
            )
            await self.customer_repository.save_async(customer)
        else:
            existing_customer.total_orders += 1
            if request.customer_address and not existing_customer.address:
                existing_customer.address = request.customer_address
            await self.customer_repository.update_async(existing_customer)
