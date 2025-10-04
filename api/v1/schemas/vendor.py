from enum import Enum
from pydantic import BaseModel, field_validator
from typing import List, Optional


class VendorType(str, Enum):
    manufacturer = 'manufacturer'
    retailer = 'retailer'
    wholesaler = 'wholesaler'
    service_provider = 'service_provider'
    

class PaymentTerms(str, Enum):
    prepaid = 'prepaid'
    postpaid = 'postpaid'
    all = 'all'
    

class VendorBase(BaseModel):

    organization_id: str
    
    unique_id: Optional[str] = None
    
    vendor_type: Optional[VendorType] = VendorType.manufacturer
    payment_terms: Optional[PaymentTerms] = PaymentTerms.all
    
    commission_percentage: Optional[float] = 0.00
    
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[str] = None
    contact_person_phone: Optional[str] = None
    contact_person_phone_country_code: Optional[str] = None
    
    @field_validator('contact_person_phone_country_code', mode='before')
    @classmethod
    def validate_contact_person_phone_country_code(cls, v, values):
        if values.data.get('phone') and not v:
            raise ValueError("contact_person_phone_country_code is required when phone is provided")
        return v

    @field_validator('contact_person_phone', mode='before')
    @classmethod
    def validate_contact_person_phone(cls, v, values):
        if values.data.get('contact_person_phone_country_code') and not v:
            raise ValueError("contact_person_phone is required when contact_person_phone_country_code is provided")
        
        if v and not v.isdigit():
            raise ValueError("Phone numbers must contain only digits")
        return v


class VendorCreate(VendorBase):
    
    category_ids: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None


class UpdateVendor(BaseModel):

    unique_id: Optional[str] = None
    category_ids: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None

    vendor_type: Optional[VendorType] = None
    payment_terms: Optional[PaymentTerms] = None
    
    commission_percentage: Optional[float] = None
    
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[str] = None
    contact_person_phone: Optional[str] = None
    contact_person_phone_country_code: Optional[str] = None
    
    @field_validator('contact_person_phone_country_code', mode='before')
    @classmethod
    def validate_contact_person_phone_country_code(cls, v, values):
        if values.data.get('phone') and not v:
            raise ValueError("contact_person_phone_country_code is required when phone is provided")
        return v

    @field_validator('contact_person_phone', mode='before')
    @classmethod
    def validate_contact_person_phone(cls, v, values):
        if values.data.get('contact_person_phone_country_code') and not v:
            raise ValueError("contact_person_phone is required when contact_person_phone_country_code is provided")
        
        if v and not v.isdigit():
            raise ValueError("Phone numbers must contain only digits")
        return v

