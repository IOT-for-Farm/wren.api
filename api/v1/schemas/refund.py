from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional


class RefundStatus(str, Enum):
    
    pending = 'pending'
    processing = 'processing'
    declined = 'declined'
    successful = 'successful'
    

class RefundBase(BaseModel):

    unique_id: Optional[str] = None
    
    organization_id: str
    payment_id: str
    amount: float
    reason: str


class UpdateRefund(BaseModel):
    
    status: RefundStatus
