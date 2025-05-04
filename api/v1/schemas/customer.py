from pydantic import BaseModel
from typing import Optional


class CustomerBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateCustomer(BaseModel):

    unique_id: Optional[str] = None


