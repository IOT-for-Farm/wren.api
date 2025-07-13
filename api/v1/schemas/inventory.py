from pydantic import BaseModel
from typing import Optional


class InventoryBase(BaseModel):

    unique_id: Optional[str] = None
    
    product_id: str
    variant_id: Optional[str] = None
    
    quantity: int
    
    reorder_threshold: Optional[int] = 5
    reorder_amount: Optional[int] = None    
    
    is_active: Optional[bool] = True


class UpdateInventory(BaseModel):

    unique_id: Optional[str] = None

    quantity: Optional[int] = None
    
    reorder_threshold: Optional[int] = None
    reorder_amount: Optional[int] = None
            
    is_active: Optional[bool] = None
