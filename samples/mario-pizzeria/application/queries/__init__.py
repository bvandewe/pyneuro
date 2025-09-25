# Query definitions and handlers auto-discovery
# Import all query modules to ensure handlers are registered during mediation setup

from .get_menu_query import GetMenuQuery, GetMenuQueryHandler
from .get_order_by_id_query import GetOrderByIdQuery, GetOrderByIdQueryHandler
from .get_orders_by_status_query import GetOrdersByStatusQuery, GetOrdersByStatusQueryHandler
from .get_active_orders_query import GetActiveOrdersQuery, GetActiveOrdersQueryHandler
from .get_kitchen_status_query import GetKitchenStatusQuery, GetKitchenStatusQueryHandler

# Make queries available for import
__all__ = [
    "GetMenuQuery",
    "GetMenuQueryHandler",
    "GetOrderByIdQuery",
    "GetOrderByIdQueryHandler",
    "GetOrdersByStatusQuery",
    "GetOrdersByStatusQueryHandler",
    "GetActiveOrdersQuery",
    "GetActiveOrdersQueryHandler",
    "GetKitchenStatusQuery",
    "GetKitchenStatusQueryHandler",
]
