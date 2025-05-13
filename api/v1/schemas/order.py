from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class OrderStatus(str, Enum):
    draft = 'draft'
    pending = 'pending'
    cancelled = 'cancelled'
    processing = 'processing'
    paid = 'paid'
    
    
class OrderItemBase(BaseModel):
    # order_id: str
    product_id: str
    quantity: int


class OrderBase(BaseModel):

    unique_id: Optional[str] = None
    organization_id: str
    # invoice_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_phone_country_code: Optional[str] = None
    customer_id: Optional[str] = None
    currency_code: Optional[str] = "NGN"
    status: Optional[OrderStatus] = OrderStatus.draft
    

class OrderCreate(OrderBase):
    order_items: List[OrderItemBase] = []


class UpdateOrder(BaseModel):

    order_items: List[OrderItemBase] = None

