from pydantic import BaseModel
from typing import Optional


class SupplierBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateSupplier(BaseModel):

    unique_id: Optional[str] = None


