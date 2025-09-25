"""Customer entity for Mario's Pizzeria domain"""

from typing import Optional
from uuid import uuid4

from neuroglia.data.abstractions import Entity


class Customer(Entity[str]):
    """Customer entity with contact information"""

    def __init__(
        self, name: str, email: str, phone: Optional[str] = None, address: Optional[str] = None
    ):
        super().__init__()
        self.id = str(uuid4())
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address

    def update_contact_info(
        self, phone: Optional[str] = None, address: Optional[str] = None
    ) -> None:
        """Update customer contact information"""
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"
