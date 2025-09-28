"""Customer entity for Mario's Pizzeria domain"""

from typing import Optional

from api.dtos import CustomerDto

from neuroglia.mapping.mapper import map_from, map_to

from ..aggregate_root import AggregateRoot
from ..events import CustomerContactUpdatedEvent, CustomerRegisteredEvent


@map_from(CustomerDto)
@map_to(CustomerDto)
class Customer(AggregateRoot):
    """Customer aggregate root with contact information"""

    def __init__(self, name: str, email: str, phone: Optional[str] = None, address: Optional[str] = None):
        super().__init__()
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address

        # Raise domain event for customer registration
        self.raise_event(CustomerRegisteredEvent(aggregate_id=self.id, name=name, email=email, phone=phone or ""))

    def update_contact_info(self, phone: Optional[str] = None, address: Optional[str] = None) -> None:
        """Update customer contact information"""
        if phone is not None and phone != self.phone:
            old_phone = self.phone or ""
            self.phone = phone

            # Raise domain event for phone update
            self.raise_event(CustomerContactUpdatedEvent(aggregate_id=self.id, field_name="phone", old_value=old_phone, new_value=phone))

        if address is not None and address != self.address:
            old_address = self.address or ""
            self.address = address

            # Raise domain event for address update
            self.raise_event(
                CustomerContactUpdatedEvent(
                    aggregate_id=self.id,
                    field_name="address",
                    old_value=old_address,
                    new_value=address,
                )
            )

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"
