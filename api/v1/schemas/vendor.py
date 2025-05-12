from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class VendorType(str, Enum):
    manufacturer = 'manufacturer'
    retailer = 'retailer'
    wholesaler = 'wholesaler'
    service_provider = 'service_provider'
    

class VendorBase(BaseModel):

    unique_id: Optional[str] = None


class VendorCreate(VendorBase):
    
    organization_id: str
    category_ids: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None


class UpdateVendor(BaseModel):

    unique_id: Optional[str] = None
    category_ids: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None


