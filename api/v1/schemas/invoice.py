from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional


class InvoiceStatus(str, Enum):
    
    pending = 'pending'
    paid = 'paid'
    overdue = 'overdue'
    cancelled = 'cancelled'
    

class InvoiceItem(BaseModel):
    rate: float
    quantity: int
    description: str
    

class InvoiceBase(BaseModel):

    unique_id: Optional[str] = None
    
    organization_id: str
    department_id: Optional[str] = None
    customer_id: Optional[str] = None
    vendor_id: Optional[str] = None
    order_id: Optional[str] = None
    currency_code: Optional[str] = 'NGN'
    due_date: Optional[datetime] = None
    items: Optional[List[InvoiceItem]] = None
    # status: Optional[InvoiceStatus] = InvoiceStatus.pending
    
    @field_validator("due_date")
    def validate_end_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date cannot be in the past.")
        return v
    

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
    recipients: Optional[List[EmailStr]] = None
    

class GenerateSaleInvoice(BaseModel):
    unique_id: Optional[str] = None
    
    organization_id: str
    department_id: Optional[str] = None
    sale_id: str
    
    currency_code: Optional[str] = 'NGN'
    
    due_date: Optional[datetime] = None
    send_notification: Optional[bool] = False
    template_id: Optional[str] = None
    context: Optional[dict] = None
    recipients: Optional[List[EmailStr]] = None
    
    @field_validator("due_date")
    def validate_end_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date cannot be in the past.")
        return v


class UpdateInvoice(BaseModel):

    due_date: Optional[datetime] = None
    status: Optional[InvoiceStatus] = None
    items: Optional[List[InvoiceItem]] = None
    
    @field_validator("due_date")
    def validate_end_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date cannot be in the past.")
        return v
