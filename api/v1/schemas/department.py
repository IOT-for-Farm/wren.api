from pydantic import BaseModel, field_validator, Field
from typing import Dict, List, Optional
from datetime import date
from enum import Enum

from api.v1.schemas.base import AdditionalInfoSchema


class DepartmentBase(BaseModel):

    unique_id: Optional[str] = None
    organization_id: str
    name: str
    parent_id: Optional[str] = None
    additional_info: Optional[List[AdditionalInfoSchema]] = None
    
    @field_validator('parent_id')
    def validate_parent_id(cls, v, values):
        if v and v == values.data.get('id'):
            raise ValueError("Department cannot be its own parent")
        return v


class UpdateDepartment(BaseModel):

    unique_id: Optional[str] = None
    name: Optional[str] = None
    parent_id: Optional[str] = None
    additional_info: Optional[List[AdditionalInfoSchema]] = None
    additional_info_keys_to_remove: Optional[List[str]] = None
    
    @field_validator('parent_id')
    def validate_parent_id(cls, v, values):
        if v and v == values.data.get('id'):
            raise ValueError("Department cannot be its own parent")
        return v


class RemoveMemberFromDepartment(BaseModel):
    
    user_id: str

class AddMemberToDepartment(RemoveMemberFromDepartment):
    
    role_id: str
    

class DepartmentRoleBase(BaseModel):
    
    role_name: str
    description: Optional[str] = None
    permissions: List[str] = []
    
    
class DepartmentRoleUpdate(BaseModel):
    
    role_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    
    
class BudgetPeriodType(str, Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"


class DepartmentBudgetBase(BaseModel):
    fiscal_year: int = Field(..., gt=2000, lt=2100, example=2024)
    period_type: str = Field(default=BudgetPeriodType.ANNUAL.value)
    allocated_amount: float = Field(..., gt=0, example=1000000.00)
    currency: str = Field(default="NGN", min_length=3, max_length=3)
    fiscal_period_start: Optional[date] = None
    fiscal_period_end: Optional[date] = None


class DepartmentBudgetUpdate(BaseModel):
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    fiscal_period_start: Optional[date] = None
    fiscal_period_end: Optional[date] = None
    amount_to_add_from_pending: Optional[float] = Field(None)
    amount_to_remove: Optional[float] = Field(None)


class BudgetAdjustmentBase(BaseModel):
    amount: float = Field(..., description="Positive for increase, negative for decrease")
    reason: str = Field(..., min_length=5, max_length=200)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v):
        if v == 0:
            raise ValueError("Amount cannot be zero")
        return v
    

class BudgetAdjustmentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class BudgetAdjustmentUpdate(BaseModel):
    status: BudgetAdjustmentStatus
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v, values):
        if v == BudgetAdjustmentStatus.PENDING:
            raise ValueError("Cannot revert to pending status")
        return v
