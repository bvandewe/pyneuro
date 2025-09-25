from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal


@dataclass
class PizzaDto:
    """Pizza data transfer object for API responses"""

    id: str
    name: str
    size: str  # "small", "medium", "large"
    base_price: str  # Formatted as currency string
    total_price: str  # Formatted as currency string
    toppings: List[str]
    preparation_time_minutes: int


@dataclass
class OrderDto:
    """Order data transfer object for API responses"""

    id: str
    customer_name: str
    customer_phone: str
    customer_address: Optional[str]
    pizzas: List[PizzaDto]
    status: str
    subtotal: str  # Formatted as currency string
    delivery_fee: str  # Formatted as currency string
    total_amount: str  # Formatted as currency string
    order_time: str  # ISO datetime string
    estimated_ready_time: Optional[str]  # ISO datetime string
    actual_ready_time: Optional[str]  # ISO datetime string
    notes: Optional[str]
    payment_method: str


@dataclass
class CustomerDto:
    """Customer data transfer object for API responses"""

    id: str
    name: str
    phone: str
    email: Optional[str]
    address: Optional[str]
    total_orders: int
    created_at: str  # ISO datetime string


@dataclass
class KitchenStatusDto:
    """Kitchen status data transfer object for API responses"""

    id: str
    active_orders: List[str]
    max_concurrent_orders: int
    current_capacity: int
    available_capacity: int
    is_busy: bool
    total_orders_processed: int


@dataclass
class CreateOrderDto:
    """DTO for creating new orders"""

    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    pizzas: List["PizzaOrderItemDto"] = None
    payment_method: str = "cash"
    delivery_fee: Optional[str] = "0.00"  # Formatted as currency string
    notes: Optional[str] = None

    def __post_init__(self):
        if self.pizzas is None:
            self.pizzas = []


@dataclass
class PizzaOrderItemDto:
    """DTO for pizza items in an order"""

    name: str
    size: str  # "small", "medium", "large"
    toppings: List[str] = None

    def __post_init__(self):
        if self.toppings is None:
            self.toppings = []


@dataclass
class CreatePizzaDto:
    """DTO for creating new pizzas"""

    name: str
    size: str
    base_price: str  # Currency string like "15.99"
    toppings: List[str] = None
    preparation_time_minutes: int = 15

    def __post_init__(self):
        if self.toppings is None:
            self.toppings = []


@dataclass
class UpdateOrderStatusDto:
    """DTO for updating order status"""

    status: str
    notes: Optional[str] = None


@dataclass
class CreateCustomerDto:
    """DTO for creating new customers"""

    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
