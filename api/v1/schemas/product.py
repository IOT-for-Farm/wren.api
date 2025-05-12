import datetime as dt
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

from api.v1.schemas.base import AdditionalInfoSchema


class ProductStatus(str, Enum):
    
    PUBLISHED = "published"
    UNPUBLISHED = "unpublished"
    DRAFT = "draft"
    UNDER_REVIEW = "review"
    
class ProductType(str, Enum):
    
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    COMPOSITE = "composite"
    OTHER = "other"


class ProductBase(BaseModel):
    unique_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    status: ProductStatus = ProductStatus.UNPUBLISHED
    type: ProductType = ProductType.PHYSICAL
    is_available: bool = True
    attributes: Optional[List[AdditionalInfoSchema]] = []
    additional_info: Optional[List[AdditionalInfoSchema]] = []
    

class ProductCreate(ProductBase):
    organization_id: str
    vendor_id: Optional[str] = None
    parent_id: Optional[str] = None
    category_ids: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None
    

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[ProductStatus] = None
    type: Optional[ProductType] = None
    is_available: Optional[bool] = None
    attributes: Optional[List[AdditionalInfoSchema]] = None
    additional_info: Optional[List[AdditionalInfoSchema]] = None
    additional_info_keys_to_remove: Optional[List[str]] = None
    attributes_keys_to_remove: Optional[List[str]] = None
    vendor_id: Optional[str] = None
    parent_id: Optional[str] = None
    category_ids: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None


class ProductVariantBase(BaseModel):
    unique_id: Optional[str] = None
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[List[AdditionalInfoSchema]] = []
    

class ProductVariantCreate(ProductVariantBase):
    product_id: str
    organization_id: str
    

class ProductVariantUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[List[AdditionalInfoSchema]] = None
    attributes_keys_to_remove: Optional[List[str]] = None
