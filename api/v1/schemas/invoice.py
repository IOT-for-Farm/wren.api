from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class InvoiceStatus(str, Enum):
    
    pending = 'pending'
    paid = 'paid'
    overdue = 'overdue'
    cancelled = 'cancelled'
    

class InvoiceBase(BaseModel):

    unique_id: Optional[str] = None
    
    organization_id: str
    department_id: Optional[str] = None
    # customer_id: Optional[str] = None
    vendor_id: Optional[str] = None
    order_id: Optional[str] = None
    
    currency_code: Optional[str] = 'NGN'
    
    due_date: Optional[datetime] = None
    # status: Optional[InvoiceStatus] = InvoiceStatus.pending
    

class GenerateInvoice(InvoiceBase):
    
    month: Optional[int] = Field(
        None,
        ge=1,  # greater than or equal to 1
        le=12,  # less than or equal to 12
        description="Month number (1-12)"
    )
    year: Optional[int] = Field(
        None,
        ge=1000,  # greater than or equal to 1
        le=datetime.now().year,  # less than or equal to the current year
        description="Year"
    )
    send_notification: Optional[bool] = False
    template_id: Optional[str] = None
    context: Optional[dict] = None


class UpdateInvoice(BaseModel):

    due_date: Optional[datetime] = None
    status: Optional[InvoiceStatus] = None
