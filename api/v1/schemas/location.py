from pydantic import BaseModel, field_validator
from typing import Optional


class LocationBase(BaseModel):
    
    unique_id: Optional[str] = None
    model_name: Optional[str] = None
    model_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    @field_validator("model_name", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v


class UpdateLocation(LocationBase):
    pass

