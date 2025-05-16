from enum import Enum
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional

from api.v1.schemas.base import AdditionalInfoSchema


class OrderStatus(str, Enum):
    draft = 'draft'
    pending = 'pending'
    cancelled = 'cancelled'
    accepted = 'accepted'
    paid = 'paid'
    failed = 'failed'
    
    
class OrderItemBase(BaseModel):
    # order_id: str
    product_id: str
    quantity: int


class OrderBase(BaseModel):

    unique_id: Optional[str] = None
    organization_id: str
    # invoice_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    customer_phone_country_code: Optional[str] = None
    customer_id: Optional[str] = None
    currency_code: Optional[str] = "NGN"
    status: Optional[OrderStatus] = OrderStatus.draft
    
    @field_validator('customer_phone_country_code', mode='before')
    @classmethod
    def validate_customer_phone_country_code(cls, v, values):
        if values.data.get('customer_phone') and not v:
            raise ValueError("customer_phone_country_code is required when customer_phone is provided")
        
        return v

    @field_validator('customer_phone', mode='before')
    @classmethod
    def validate_customer_phone(cls, v, values):
        if values.data.get('customer_phone_country_code') and not v:
            raise ValueError("customer_phone is required when customer_phone_country_code is provided")
        
        if v and not v.isdigit():
            raise ValueError("Phone numbers must contain only digits")
        
        return v
    
    @field_validator('customer_name', mode='before')
    @classmethod
    def validate_customer_name(cls, v, values):
        if not values.data.get('customer_id') and not v:
            raise ValueError("customer_name is required when customer_id is not provided")

        return v
    
    @field_validator('customer_email', mode='before')
    @classmethod
    def validate_customer_email(cls, v, values):
        if not values.data.get('customer_id') and not v:
            raise ValueError("customer_email is required when customer_id is not provided")

        return v
    

class OrderCreate(OrderBase):
    order_items: List[OrderItemBase] = []
    additional_info: Optional[List[AdditionalInfoSchema]] = None


class UpdateOrder(BaseModel):

    status: Optional[OrderStatus] = None
    order_items: Optional[List[OrderItemBase]] = None
    additional_info: Optional[List[AdditionalInfoSchema]] = None
    additional_info_keys_to_remove: Optional[List[str]] = None
