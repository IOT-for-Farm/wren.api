from enum import Enum
from pydantic import BaseModel
from typing import Optional


class OrderStatus(str, Enum):
    draft = 'draft'
    pending = 'pending'
    paid = 'paid'


class OrderBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateOrder(BaseModel):

    unique_id: Optional[str] = None


