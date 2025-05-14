from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import datetime as dt

    
class UpdateUser(BaseModel):
    
    email: Optional[EmailStr] = None
    old_password: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_country_code: Optional[str] = None
    profile_picture: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    
    @field_validator("email", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v
    
    @field_validator('phone_country_code', mode='before')
    @classmethod
    def validate_phone_country_code(cls, v, values):
        if values.data.get('phone') and not v:
            raise ValueError("phone_country_code is required when phone is provided")
        return v

    @field_validator('phone_number', mode='before')
    @classmethod
    def validate_phone_number(cls, v, values):
        if values.data.get('phone_country_code') and not v:
            raise ValueError("phone is required when phone_country_code is provided")
        
        if v and not v.isdigit():
            raise ValueError("Phone numbers must contain only digits")
        return v
    
    
class AccountReactivationRequest(BaseModel):
    
    email: EmailStr
    
    @field_validator("email", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v
