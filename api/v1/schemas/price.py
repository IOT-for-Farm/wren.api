from pydantic import BaseModel
from typing import Optional


class PriceBase(BaseModel):

    unique_id: Optional[str] = None


class UpdatePrice(BaseModel):

    unique_id: Optional[str] = None


