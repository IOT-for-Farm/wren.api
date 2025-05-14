from pydantic import BaseModel
from typing import List, Optional


class CategoryBase(BaseModel):

    unique_id: Optional[str] = None
    organization_id: str
    name: str
    model_type: str
    description: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class UpdateCategory(BaseModel):

    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None


class AttachOrDetatchCategory(BaseModel):
    
    category_ids: List[str]
    entity_id: str
    model_type: str
