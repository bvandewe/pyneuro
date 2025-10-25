"""
Order event handlers for Mario's Pizzeria.

These handlers process order-related domain events to implement side effects like
notifications, kitchen updates, delivery tracking, and customer communications.
"""

import logging

from application.events.base_domain_event_handler import BaseDomainEventHandler
from domain.events import (
    CookingStartedEvent,
    OrderCancelledEvent,
    OrderConfirmedEvent,
    OrderDeliveredEvent,
    OrderReadyEvent,
    PizzaAddedToOrderEvent,
    PizzaRemovedFromOrderEvent,
)

from neuroglia.eventing.cloud_events.infrastructure import CloudEventBus
from neuroglia.eventing.cloud_events.infrastructure.cloud_event_publisher import (
    CloudEventPublishingOptions,
)
from neuroglia.mediation import DomainEventHandler, Mediator

# Set up logger
logger = logging.getLogger(__name__)


class OrderConfirmedEventHandler(BaseDomainEventHandler[OrderConfirmedEvent], DomainEventHandler[OrderConfirmedEvent]):
    """Handles order confirmation events - sends notifications and updates kitchen"""

    def __init__(
        self,
        mediator: Mediator,
        cloud_event_bus: CloudEventBus,
        cloud_event_publishing_options: CloudEventPublishingOptions,
    ):
        super().__init__(mediator, cloud_event_bus, cloud_event_publishing_options)

    async def handle_async(self, event: OrderConfirmedEvent) -> None:
        """Process order confirmed event"""
        logger.info(f"🍕 Order {event.aggregate_id} confirmed! " f"Total: ${event.total_amount}, Pizzas: {event.pizza_count}")

        # In a real application, you might:
        # - Send SMS notification to customer
        # - Send email receipt
        # - Notify kitchen display system
        # - Update analytics/reporting databases
        # - Create kitchen ticket

        await self.publish_cloud_event_async(event)
        return None


class CookingStartedEventHandler(BaseDomainEventHandler[CookingStartedEvent], DomainEventHandler[CookingStartedEvent]):
    """Handles cooking started events - updates kitchen display and estimated times"""

    async def handle_async(self, event: CookingStartedEvent) -> None:
        """Process cooking started event"""
        logger.info(f"👨‍🍳 Cooking started for order {event.aggregate_id} at {event.cooking_started_time}")

        # In a real application, you might:
        # - Update kitchen display system
        # - Calculate and update estimated ready time
        # - Send "cooking started" notification to customer
        # - Update order tracking system

        await self.publish_cloud_event_async(event)
        return None


class OrderReadyEventHandler(BaseDomainEventHandler[OrderReadyEvent], DomainEventHandler[OrderReadyEvent]):
    """Handles order ready events - notifies customer and updates pickup systems"""

    async def handle_async(self, event: OrderReadyEvent) -> None:
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

        # Publish as CloudEvent for external integrations
        await self.publish_cloud_event_async(event)
        return None


class OrderDeliveredEventHandler(BaseDomainEventHandler[OrderDeliveredEvent], DomainEventHandler[OrderDeliveredEvent]):
    """Handles order delivered events - completes the order lifecycle"""

    async def handle_async(self, event: OrderDeliveredEvent) -> None:
        """Process order delivered event"""
        logger.info(f"🎉 Order {event.aggregate_id} delivered successfully at {event.delivered_time}")

        # In a real application, you might:
        # - Send delivery confirmation and feedback request
        # - Update customer order history
        # - Process payment (if not already processed)
        # - Update loyalty points/rewards
        # - Archive order data
        # - Generate delivery analytics

        # Publish as CloudEvent for external integrations
        await self.publish_cloud_event_async(event)
        return None


class OrderCancelledEventHandler(BaseDomainEventHandler[OrderCancelledEvent], DomainEventHandler[OrderCancelledEvent]):
    """Handles order cancelled events - manages refunds and notifications"""

    async def handle_async(self, event: OrderCancelledEvent) -> None:
        """Process order cancelled event"""
        reason_msg = f" (Reason: {event.reason})" if event.reason else ""
        logger.info(f"❌ Order {event.aggregate_id} cancelled at {event.cancelled_time}{reason_msg}")

        # In a real application, you might:
        # - Process refund if payment was already taken
        # - Send cancellation notification to customer
        # - Remove from kitchen queue if not started cooking
        # - Update inventory if ingredients were allocated
        # - Log cancellation reasons for analysis

        # Publish as CloudEvent for external integrations
        await self.publish_cloud_event_async(event)
        return None


class PizzaAddedToOrderEventHandler(BaseDomainEventHandler[PizzaAddedToOrderEvent], DomainEventHandler[PizzaAddedToOrderEvent]):
    """Handles pizza additions to orders"""

    async def handle_async(self, event: PizzaAddedToOrderEvent) -> None:
        """Process pizza added to order event"""
        logger.info(f"🍕 Added {event.pizza_size} {event.pizza_name} (${event.price}) " f"to order {event.aggregate_id}")

        # In a real application, you might:
        # - Update real-time order display for customer
        # - Check ingredient availability
        # - Update order total in UI
        # - Log popular pizza combinations
        await self.publish_cloud_event_async(event)
        return None


class PizzaRemovedFromOrderEventHandler(BaseDomainEventHandler[PizzaRemovedFromOrderEvent], DomainEventHandler[PizzaRemovedFromOrderEvent]):
    """Handles pizza removals from orders"""

    async def handle_async(self, event: PizzaRemovedFromOrderEvent) -> None:
        """Process pizza removed from order event"""
        logger.info(f"Removed line item {event.line_item_id} from order {event.aggregate_id}")

        # In a real application, you might:
        # - Update real-time order display for customer
        # - Release reserved ingredients
        # - Update order total in UI
        # - Log customer behavior patterns

        # Publish as CloudEvent for external integrations
        await self.publish_cloud_event_async(event)
        return None
