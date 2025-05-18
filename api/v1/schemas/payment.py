from enum import Enum
from pydantic import BaseModel
from typing import Optional


class PaymentStatus(str, Enum):
    
    successful = 'successful'
    failed = 'failed'
    pending = 'pending'
    processing = 'processing'
    cancelled = 'cancelled'
    refunded = 'refunded'
    
    
class PaymentMethod(str, Enum):
    
    cash = 'cash'
    bank_transfer = 'bank_transfer'
    card = 'card'


class PaymentBase(BaseModel):

    unique_id: Optional[str] = None
    organization_id: str
    invoice_id: str
    amount: int
    currency_code: str = 'NGN'
    method: Optional[PaymentMethod] = PaymentMethod.cash
    narration: Optional[str] = None
    status: Optional[PaymentStatus] = PaymentStatus.pending


class UpdatePayment(BaseModel):

    status: Optional[PaymentStatus] = None
