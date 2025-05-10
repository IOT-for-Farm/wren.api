from enum import Enum
from pydantic import BaseModel
from typing import Optional


class RefundStatus(str, Enum):
    
    pending = 'pending'
    processed = 'processed'
    declined = 'declined'
    

class RefundBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateRefund(BaseModel):

    unique_id: Optional[str] = None


