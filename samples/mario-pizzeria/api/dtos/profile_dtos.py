"""DTOs for customer profile management"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerProfileDto(BaseModel):
    """DTO for customer profile information"""

    id: Optional[str] = None
    user_id: str  # Keycloak user ID
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    address: Optional[str] = Field(None, max_length=200)

    # Order statistics (read-only)
    total_orders: int = 0
    favorite_pizza: Optional[str] = None

    class Config:
        from_attributes = True


class CreateProfileDto(BaseModel):
    """DTO for creating a new customer profile"""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    address: Optional[str] = Field(None, max_length=200)


class UpdateProfileDto(BaseModel):
    """DTO for updating customer profile"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    address: Optional[str] = Field(None, max_length=200)
