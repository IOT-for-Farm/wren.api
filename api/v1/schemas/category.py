from pydantic import BaseModel, field_validator
from typing import List, Optional


class CategoryBase(BaseModel):

    unique_id: Optional[str] = None
    organization_id: str
    name: str
    model_type: str
    description: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None
    
    @field_validator("name", "model_type", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v


class UpdateCategory(BaseModel):

    name: Optional[str] = None
    description: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None
    
    @field_validator("name", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v


class AttachOrDetatchCategory(BaseModel):
    
    category_ids: List[str]
    entity_id: str
    model_type: str
