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

class CustomerBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateCustomer(BaseModel):

    unique_id: Optional[str] = None


