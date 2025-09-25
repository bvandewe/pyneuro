# Command definitions and handlers auto-discovery
# Import all command modules to ensure handlers are registered during mediation setup

from .place_order_command import PlaceOrderCommand, PlaceOrderCommandHandler
from .start_cooking_command import StartCookingCommand, StartCookingCommandHandler
from .complete_order_command import CompleteOrderCommand, CompleteOrderCommandHandler

# Make commands available for import
__all__ = [
    "PlaceOrderCommand",
    "PlaceOrderCommandHandler",
    "StartCookingCommand",
    "StartCookingCommandHandler",
    "CompleteOrderCommand",
    "CompleteOrderCommandHandler",
]
