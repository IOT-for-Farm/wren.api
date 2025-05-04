from pydantic import BaseModel, field_validator, constr
from typing import Optional
from enum import Enum


class ContactType(str, Enum):
    PHONE = "phone"
    EMAIL = "email"
    OTHER = "other"

class ContactInfoBase(BaseModel):
    unique_id: Optional[str] = None
    model_name: Optional[str] = None
    model_id: Optional[str] = None
    contact_type: ContactType  # Using enum for strict type control
    contact_data: str
    phone_country_code: Optional[str] = None
    is_primary: bool = False
    
    @field_validator("model_name", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator('phone_country_code', mode='before')
    @classmethod
    def validate_phone_country_code(cls, v, values):
        if values.data.get('contact_type') == ContactType.PHONE and not v:
            raise ValueError("phone_country_code is required when contact_type is 'phone'")
        return v

    @field_validator('contact_data', mode='before')
    @classmethod
    def validate_contact_data(cls, v, values):
        contact_type = values.data.get('contact_type')
        if contact_type == ContactType.PHONE:
            if not v.isdigit():
                raise ValueError("Phone numbers must contain only digits")
        elif contact_type == ContactType.EMAIL:
            if '@' not in v:
                raise ValueError("Invalid email format")
        return v


class UpdateContactInfo(BaseModel):

    unique_id: Optional[str] = None
    contact_data: Optional[str] = None
    phone_country_code: Optional[str] = None
    is_primary: bool = False
