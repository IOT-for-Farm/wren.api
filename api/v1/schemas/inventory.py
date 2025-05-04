from pydantic import BaseModel
from typing import Optional


class InventoryBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateInventory(BaseModel):

    unique_id: Optional[str] = None


