from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TagBase(BaseModel):

    organization_id: str
    name: str = Field(min_length=1, max_length=100)
    model_type: str = Field(min_length=1, max_length=100)
    parent_id: Optional[str] = None
    group: Optional[str] = None
    
    @field_validator("name", "model_type", "group", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v


class UpdateTag(BaseModel):

    name: Optional[str] = None
    model_type: Optional[str] = None
    parent_id: Optional[str] = None
    group: Optional[str] = None
    
    @field_validator("name", "model_type", "group", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v
