from enum import Enum
from pydantic import BaseModel
from typing import Optional


class VendorType(str, Enum):
    manufacturer = 'manufacturer'
    retailer = 'retailer'
    wholesaler = 'wholesaler'
    service_provider = 'service_provider'
    

class VendorBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateVendor(BaseModel):

    unique_id: Optional[str] = None


