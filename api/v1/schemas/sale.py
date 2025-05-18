from pydantic import BaseModel
from typing import List, Optional


class SaleBase(BaseModel):

    unique_id: Optional[str] = None


class SaleCreate(SaleBase):
    
    organization_id: str
    # category_ids: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None

class UpdateSale(BaseModel):

    # category_ids: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None


