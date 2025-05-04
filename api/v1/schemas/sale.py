from pydantic import BaseModel
from typing import Optional


class SaleBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateSale(BaseModel):

    unique_id: Optional[str] = None


