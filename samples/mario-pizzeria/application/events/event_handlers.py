"""
Event handlers for Mario's Pizzeria domain events.

These handlers process domain events to implement side effects like notifications,
logging, updating read models, and other cross-cutting concerns.
"""

import logging
from typing import Any

from domain.events import (
    CookingStartedEvent,
    CustomerContactUpdatedEvent,
    CustomerRegisteredEvent,
    OrderCancelledEvent,
    OrderConfirmedEvent,
    OrderDeliveredEvent,
    OrderReadyEvent,
    PizzaAddedToOrderEvent,
    PizzaRemovedFromOrderEvent,
)

from neuroglia.mediation import DomainEventHandler

# Set up logger
logger = logging.getLogger(__name__)


class OrderConfirmedEventHandler(DomainEventHandler[OrderConfirmedEvent]):
    """Handles order confirmation events - sends notifications and updates kitchen"""

    async def handle_async(self, event: OrderConfirmedEvent) -> Any:
        """Process order confirmed event"""
        logger.info(f"🍕 Order {event.aggregate_id} confirmed! " f"Total: ${event.total_amount}, Pizzas: {event.pizza_count}")

        # In a real application, you might:
        # - Send SMS notification to customer
        # - Send email receipt
        # - Notify kitchen display system
        # - Update analytics/reporting databases
        # - Create kitchen ticket

        return None


class CookingStartedEventHandler(DomainEventHandler[CookingStartedEvent]):
    """Handles cooking started events - updates kitchen display and estimated times"""

    async def handle_async(self, event: CookingStartedEvent) -> Any:
        """Process cooking started event"""
        logger.info(f"👨‍🍳 Cooking started for order {event.aggregate_id} at {event.cooking_started_time}")

        # In a real application, you might:
        # - Update kitchen display system
        # - Calculate and update estimated ready time
        # - Send "cooking started" notification to customer
        # - Update order tracking system

        return None


class OrderReadyEventHandler(DomainEventHandler[OrderReadyEvent]):
    """Handles order ready events - notifies customer and updates pickup systems"""

    async def handle_async(self, event: OrderReadyEvent) -> Any:
        """Process order ready event"""
        logger.info(f"✅ Order {event.aggregate_id} is ready for pickup/delivery! " f"Ready at: {event.ready_time}")

        # Calculate timing performance
        if event.estimated_ready_time:
            actual_minutes = (event.ready_time - event.estimated_ready_time).total_seconds() / 60
            if actual_minutes > 5:
                logger.warning(f"⏰ Order {event.aggregate_id} was {actual_minutes:.1f} minutes late")
            elif actual_minutes < -5:
                logger.info(f"🚀 Order {event.aggregate_id} was ready {-actual_minutes:.1f} minutes early")

        # In a real application, you might:
        # - Send "order ready" SMS/push notification to customer
        # - Update pickup/delivery queue
        # - Print receipt/pickup ticket
        # - Update customer app with pickup code
        # - Log performance metrics for kitchen efficiency

        return None


class OrderDeliveredEventHandler(DomainEventHandler[OrderDeliveredEvent]):
    """Handles order delivered events - completes the order lifecycle"""

    async def handle_async(self, event: OrderDeliveredEvent) -> Any:
        """Process order delivered event"""
        logger.info(f"🎉 Order {event.aggregate_id} delivered successfully at {event.delivered_time}")

        # In a real application, you might:
        # - Send delivery confirmation and feedback request
        # - Update customer order history
        # - Process payment (if not already processed)
        # - Update loyalty points/rewards
        # - Archive order data
        # - Generate delivery analytics

        return None


class OrderCancelledEventHandler(DomainEventHandler[OrderCancelledEvent]):
    """Handles order cancelled events - manages refunds and notifications"""

    async def handle_async(self, event: OrderCancelledEvent) -> Any:
        """Process order cancelled event"""
        reason_msg = f" (Reason: {event.reason})" if event.reason else ""
        logger.info(f"❌ Order {event.aggregate_id} cancelled at {event.cancelled_time}{reason_msg}")

        # In a real application, you might:
        # - Process refund if payment was already taken
        # - Send cancellation notification to customer
        # - Remove from kitchen queue if not started cooking
        # - Update inventory if ingredients were allocated
        # - Log cancellation reasons for analysis

        return None


class CustomerRegisteredEventHandler(DomainEventHandler[CustomerRegisteredEvent]):
    """Handles new customer registration events"""

    async def handle_async(self, event: CustomerRegisteredEvent) -> Any:
        """Process customer registered event"""
        logger.info(f"👋 New customer registered: {event.name} ({event.email}) - ID: {event.aggregate_id}")

        # In a real application, you might:
        # - Send welcome email/SMS
        # - Create loyalty account
        # - Add to marketing lists (with consent)
        # - Send first-order discount code
        # - Update customer analytics

        return None


class CustomerContactUpdatedEventHandler(DomainEventHandler[CustomerContactUpdatedEvent]):
    """Handles customer contact information updates"""

    async def handle_async(self, event: CustomerContactUpdatedEvent) -> Any:
        """Process customer contact updated event"""
        logger.info(f"📝 Customer {event.aggregate_id} updated {event.field_name}: " f"{event.old_value} → {event.new_value}")

        # In a real application, you might:
        # - Update external CRM systems
        # - Validate new contact information
        # - Send confirmation to new phone/email
        # - Update marketing preferences
        # - Audit contact changes for compliance

        return None


class PizzaAddedToOrderEventHandler(DomainEventHandler[PizzaAddedToOrderEvent]):
    """Handles pizza additions to orders"""

    async def handle_async(self, event: PizzaAddedToOrderEvent) -> Any:
        """Process pizza added to order event"""
        logger.info(f"🍕 Added {event.pizza_size} {event.pizza_name} (${event.price}) " f"to order {event.aggregate_id}")

        # In a real application, you might:
        # - Update real-time order display for customer
        # - Check ingredient availability
        # - Update order total in UI
        # - Log popular pizza combinations

        return None


class PizzaRemovedFromOrderEventHandler(DomainEventHandler[PizzaRemovedFromOrderEvent]):
    """Handles pizza removals from orders"""

    async def handle_async(self, event: PizzaRemovedFromOrderEvent) -> Any:
        """Process pizza removed from order event"""
        logger.info(f"➖ Removed line item {event.line_item_id} from order {event.aggregate_id}")

        # In a real application, you might:
        # - Update real-time order display for customer
        # - Release reserved ingredients
        # - Update order total in UI
        # - Log customer behavior patterns

        return None
