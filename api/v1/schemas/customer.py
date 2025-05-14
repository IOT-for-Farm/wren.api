from enum import Enum
from pydantic import BaseModel
from typing import Optional


class IndustryEnum(str, Enum):
    agriculture = "agriculture"
    automotive = "automotive"
    banking = "banking"
    construction = "construction"
    education = "education"
    energy = "energy"
    entertainment = "entertainment"
    fashion = "fashion"
    finance = "finance"
    food_and_beverage = "food and beverage"
    government = "government"
    healthcare = "healthcare"
    hospitality = "hospitality"
    insurance = "insurance"
    legal = "legal"
    logistics = "logistics"
    manufacturing = "manufacturing"
    media = "media"
    mining = "mining"
    non_profit = "non-profit"
    pharmaceutical = "pharmaceutical"
    real_estate = "real estate"
    retail = "retail"
    software = "software"
    telecommunications = "telecommunications"
    transportation = "transportation"
    travel = "travel"
    utilities = "utilities"
    wholesale = "wholesale"
    other = "other"
    

class CustomerType(str, Enum):
    
    individual = 'individual'
    business = 'business'

    
class PaymentMethod(str, Enum):
    
    cash = 'cash'
    bank_transfer = 'bank_transfer'
    card = 'card'
    

class Gender(str, Enum):
    
    male = 'male'
    female = 'female'
    

class CustomerBase(BaseModel):

    unique_id: Optional[str] = None
    
    language: Optional[str] = 'English'
    gender: Optional[Gender] = None
    age: Optional[int] = None
    
    customer_type: Optional[CustomerType] = CustomerType.individual
    industry: Optional[IndustryEnum] = None
    preferred_payment_method: Optional[PaymentMethod] = PaymentMethod.cash

class UpdateCustomer(BaseModel):

    language: Optional[str] = None
    gender: Optional[Gender] = None
    age: Optional[int] = None
    
    customer_type: Optional[CustomerType] = None
    industry: Optional[IndustryEnum] = None
    preferred_payment_method: Optional[PaymentMethod] = None
