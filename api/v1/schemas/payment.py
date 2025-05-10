from enum import Enum
from pydantic import BaseModel
from typing import Optional


class PaymentStatus(str, Enum):
    
    successful = 'successful'
    failed = 'failed'
    pending = 'pending'
    processing = 'processing'
    
    
class PaymentMethod(str, Enum):
    
    cash = 'cash'
    bank_transfer = 'bank_transfer'
    card = 'card'


class PaymentBase(BaseModel):

    unique_id: Optional[str] = None


class UpdatePayment(BaseModel):

    unique_id: Optional[str] = None


