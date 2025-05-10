from enum import Enum
from pydantic import BaseModel
from typing import Optional


class InvoiceStatus(str, Enum):
    
    pending = 'pending'
    paid = 'paid'
    overdue = 'overdue'
    cancelled = 'cancelled'
    

class InvoiceBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateInvoice(BaseModel):

    unique_id: Optional[str] = None


