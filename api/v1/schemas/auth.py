from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
import datetime as dt

from api.v1.models.apikey import Apikey
from api.v1.models.organization import Organization
from api.v1.models.user import User


class CreateUser(BaseModel):
    
    email: EmailStr
    password: Optional[str] = None
    first_name: str
    last_name: str
    phone_country_code: Optional[str] = None
    profile_picture: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    is_superuser: Optional[bool] = False
    
    @field_validator("email", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v
    
class LoginSchema(BaseModel):
    
    email: EmailStr
    password: str
    
    @field_validator("email", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v
    

class EmailRequest(BaseModel):
    
    email: EmailStr
    
    @field_validator("email", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v
    

class MagicLoginRequest(EmailRequest):
    pass
    
    
class ResetPasswordRequest(EmailRequest):
    pass


class ResetPassword(BaseModel):
    password: str

    
class GoogleAuth(BaseModel):
    id_token: str
    

class EntityType(str, Enum):
    
    APIKEY = 'apikey'
    USER = 'user'

    
class AuthenticatedEntity(BaseModel):
    
    type: EntityType
    # entity: User | Organization
    entity: User | Apikey
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
