from enum import Enum
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional

from api.v1.schemas.base import AdditionalInfoSchema


class BusinessPartnerType(str, Enum):
    
    vendor = 'vendor'
    customer = 'customer'


class BusinessPartnerBase(BaseModel):

    unique_id: Optional[str] = None
    slug: Optional[str] = None
    
    organization_id: str
    user_id: Optional[str] = None
    partner_type: Optional[BusinessPartnerType] = BusinessPartnerType.vendor

    first_name: str
    last_name: str
    phone: Optional[str] = None
    phone_country_code: Optional[str] = None
    image_url: Optional[str] = None

    email: EmailStr
    password: Optional[str] = None

    company_name: Optional[str] = None
    is_active: Optional[bool] = True

    additional_info: Optional[List[AdditionalInfoSchema]] = []
    notes: Optional[str] = None
    
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
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

    @field_validator('phone', mode='before')
    @classmethod
    def validate_phone(cls, v, values):
        if values.data.get('phone_country_code') and not v:
            raise ValueError("phone is required when phone_country_code is provided")
        
        if v and not v.isdigit():
            raise ValueError("Phone numbers must contain only digits")
        return v
    

class UpdateBusinessPartner(BaseModel):

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    phone_country_code: Optional[str] = None
    image_url: Optional[str] = None

    email: Optional[EmailStr] = None
    password: Optional[str] = None

    company_name: Optional[str] = None
    is_active: Optional[bool] = None

    notes: Optional[str] = None

    additional_info: Optional[List[AdditionalInfoSchema]] = None
    additional_info_keys_to_remove: Optional[List[str]] = None
    
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

    @field_validator('phone', mode='before')
    @classmethod
    def validate_phone(cls, v, values):
        if values.data.get('phone_country_code') and not v:
            raise ValueError("phone is required when phone_country_code is provided")
        
        if v and not v.isdigit():
            raise ValueError("Phone numbers must contain only digits")
        return v


class BusinessPartnerLogin(BaseModel):
    
    email: EmailStr
    password: Optional[str] = None


class AttachUserToBusinessPartners(BaseModel):
    
    user_id: Optional[str] = None
    business_partner_ids: List[str] = []