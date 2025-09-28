"""Place Order Command and Handler for Mario's Pizzeria"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from api.dtos import CreateOrderDto, CreatePizzaDto, OrderDto, PizzaDto
from domain.entities import Customer, Order, Pizza, PizzaSize
from domain.repositories import ICustomerRepository, IOrderRepository

from neuroglia.core import OperationResult
from neuroglia.data.unit_of_work import IUnitOfWork
from neuroglia.mapping import Mapper
from neuroglia.mapping.mapper import map_from
from neuroglia.mediation import Command, CommandHandler


@dataclass
@map_from(CreateOrderDto)
class PlaceOrderCommand(Command[OperationResult[OrderDto]]):
    """Command to place a new pizza order"""

    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    customer_email: Optional[str] = None
    pizzas: list[CreatePizzaDto] = field(default_factory=list)
    payment_method: str = "cash"
    notes: Optional[str] = None


class PlaceOrderCommandHandler(CommandHandler[PlaceOrderCommand, OperationResult[OrderDto]]):
    """Handler for placing new pizza orders"""

    def __init__(
        self,
        order_repository: IOrderRepository,
        customer_repository: ICustomerRepository,
        mapper: Mapper,
        unit_of_work: IUnitOfWork,
    ):
        self.order_repository = order_repository
        self.customer_repository = customer_repository
        self.mapper = mapper
        self.unit_of_work = unit_of_work

    async def handle_async(self, request: PlaceOrderCommand) -> OperationResult[OrderDto]:
        try:
            # First create or get customer
            customer = await self._create_or_get_customer(request)

            # Create order with customer_id
            order = Order(customer_id=customer.id)
            if request.notes:
                order.notes = request.notes

            # Add pizzas to order
            for pizza_item in request.pizzas:
                # Convert size string to enum
                size = PizzaSize(pizza_item.size.lower())

                # Create pizza with base pricing
                base_price = Decimal("12.99")  # Default base price
                if pizza_item.name.lower() == "margherita":
                    base_price = Decimal("12.99")
                elif pizza_item.name.lower() == "pepperoni":
                    base_price = Decimal("14.99")
                elif pizza_item.name.lower() == "supreme":
                    base_price = Decimal("17.99")

                pizza = Pizza(
                    name=pizza_item.name,
                    base_price=base_price,
                    size=size,
                )

                # Add toppings
                for topping in pizza_item.toppings:
                    pizza.add_topping(topping)

                order.add_pizza(pizza)

            # Validate order has pizzas
            if not order.pizzas:
                return self.bad_request("Order must contain at least one pizza")

            # Confirm order (raises domain event)
            order.confirm_order()

            # Save order
            await self.order_repository.add_async(order)

            # Register aggregates with Unit of Work for domain event dispatching
            # Note: Unit of Work uses duck typing internally to collect domain events
            from typing import cast

            from neuroglia.data.abstractions import AggregateRoot as NeuroAggregateRoot

            self.unit_of_work.register_aggregate(cast(NeuroAggregateRoot, order))
            self.unit_of_work.register_aggregate(cast(NeuroAggregateRoot, customer))

            # Create OrderDto with customer information
            order_dto = OrderDto(
                id=order.id,
                customer_name=customer.name,
                customer_phone=customer.phone,
                customer_address=customer.address,
                pizzas=[self.mapper.map(pizza, PizzaDto) for pizza in order.pizzas],
                status=order.status.value,
                order_time=order.order_time,
                confirmed_time=order.confirmed_time,
                cooking_started_time=order.cooking_started_time,
                actual_ready_time=order.actual_ready_time,
                estimated_ready_time=order.estimated_ready_time,
                notes=order.notes,
                total_amount=order.total_amount,
                pizza_count=order.pizza_count,
                payment_method=request.payment_method,
            )
            return self.created(order_dto)

        except ValueError as e:
            return self.bad_request(str(e))
        except Exception as e:
            return self.bad_request(f"Failed to place order: {str(e)}")

    async def _create_or_get_customer(self, request: PlaceOrderCommand) -> Customer:
        """Create or get customer record"""
        # Try to find existing customer by phone
        existing_customer = await self.customer_repository.get_by_phone_async(request.customer_phone)

        if existing_customer:
            # Update address if provided and customer doesn't have one
            if request.customer_address and not existing_customer.address:
                existing_customer.update_contact_info(address=request.customer_address)
                await self.customer_repository.update_async(existing_customer)
                # Register updated customer for domain events
                from typing import cast

                from neuroglia.data.abstractions import (
                    AggregateRoot as NeuroAggregateRoot,
                )

                self.unit_of_work.register_aggregate(cast(NeuroAggregateRoot, existing_customer))
            return existing_customer
        else:
            # Create new customer
            customer = Customer(
                name=request.customer_name,
                email=request.customer_email or f"{request.customer_phone}@placeholder.com",
                phone=request.customer_phone,
                address=request.customer_address,
            )
            await self.customer_repository.add_async(customer)
            return customer
