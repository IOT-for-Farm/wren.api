from enum import Enum
from pydantic import BaseModel, field_validator
from typing import Optional


class AccessType(str, Enum):
    FULL = 'full'
    LIMITED = 'limited'
    
    
class ApikeyBase(BaseModel):
    
    app_name: str
    organization_id: str
    role_id: Optional[str] = None
    access_type: str = AccessType.FULL.value
    
    @field_validator('role_id', mode='before')
    def validate_role_id(cls, v, values):
        if values.data.get('access_type') == AccessType.LIMITED.value and not v:
            raise ValueError("role_id is required when access_type is 'limited'")
        return v

class UpdateApikey(BaseModel):
    
    app_name: Optional[str] = None
    role_id: Optional[str] = None
    is_active: Optional[bool] = None
