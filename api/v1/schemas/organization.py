from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
from enum import Enum

# from api.v1.schemas.base import ContactInfoSchema, LocationSchema, OrganizationRoleSchema, OrganizationSchema, UserSchema


class BusinessType(str, Enum):
    RETAIL = 'retail'
    HOSPITALITY = 'hospitality'
    MANUFACTURING = 'manufacturing'
    CONSTRUCTION = 'construction'
    EDUCATION = 'education'
    HEALTHCARE = 'healthcare'
    TRANSPORTATION = 'transportation'
    AGRICULTURE = 'agriculture'
    FINANCE = 'finance'
    REAL_ESTATE = 'real estate'
    INFORMATION_TECHNOLOGY = 'information technology'
    TELECOMMUNICATIONS = 'telecommunications'
    ENTERTAINMENT = 'entertainment'
    GOVERNMENT = 'government'
    NON_PROFIT = 'non-profit'
    LOGISTICS = 'logistics'
    INSURANCE = 'insurance'
    MARKETING = 'marketing'
    MEDIA = 'media'
    MINING = 'mining'
    TOURISM = 'tourism'
    OTHER = 'other'
    
    
class SocialMediaLink(BaseModel):
    platform: str
    link: str
    
    
class OrganizationBase(BaseModel):
    
    unique_id: Optional[str] = None
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    social_media_links: Optional[List[SocialMediaLink]] = None
    policy: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    initials: Optional[str] = None
    tagline: Optional[str] = None
    business_type: Optional[str] = BusinessType.RETAIL.value
    timezone: Optional[str] = None
    currency: Optional[str] = None


class CreateOrganization(OrganizationBase):
    
    email: EmailStr
    phone: Optional[str] = None
    phone_country_code: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    address: str
    
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

class UpdateOrganization(BaseModel):
    
    unique_id: Optional[str] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    social_media_links: Optional[List[SocialMediaLink]] = None
    policy: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    initials: Optional[str] = None
    tagline: Optional[str] = None
    business_type: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    

class InviteUser(BaseModel):
    
    email: EmailStr
    role_id: str
    
    
class CreateRole(BaseModel):
    
    role_name: str
    permissions: List[str] = []


class UpdateRole(BaseModel):
    
    role_name: Optional[str] = None
    permissions: Optional[List[str]] = None
    

class ActivateOrDeactivateMember(BaseModel):
    
    user_id: str
    

class AssignRole(BaseModel):
    
    organization_id: str
    user_id: str
    role_id: str
    


# class OrganizationResponse(OrganizationSchema):
#     creator: UserSchema # type: ignore
#     contact_infos: List[ContactInfoSchema] # type: ignore
#     locations: List[LocationSchema] # type: ignore
#     roles: List[OrganizationRoleSchema] # type: ignore
