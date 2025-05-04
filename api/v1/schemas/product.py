from enum import Enum
from pydantic import BaseModel
from typing import Optional


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


class UpdateProduct(BaseModel):

    unique_id: Optional[str] = None


