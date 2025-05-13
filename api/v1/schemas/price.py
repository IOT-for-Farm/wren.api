import datetime as dt
from decimal import Decimal
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional


class PriceBase(BaseModel):
    cost_price: Decimal
    selling_price: Decimal
    currency: str = "NGN"
    start_date: Optional[dt.datetime] = None
    end_date: Optional[dt.datetime] = None
    min_quantity: Optional[int] = 1
    is_active: bool = True
    notes: Optional[str] = None
    
    @field_validator("start_date")
    def validate_start_date(cls, v):
        if v and v < dt.datetime.now():
            raise ValueError("Start date cannot be in the past.")
        return v

    @field_validator("end_date")
    def validate_end_date(cls, v):
        if v and v < dt.datetime.now():
            raise ValueError("End date cannot be in the past.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date.")
        return self
    

class PriceCreate(PriceBase):
    product_id: str
    variant_id: Optional[str] = None
    

class PriceUpdate(BaseModel):
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    currency: Optional[str] = None
    start_date: Optional[dt.datetime] = None
    end_date: Optional[dt.datetime] = None
    min_quantity: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    
    @field_validator("start_date")
    def validate_start_date(cls, v):
        if v and v < dt.datetime.now():
            raise ValueError("Start date cannot be in the past.")
        return v

    @field_validator("end_date")
    def validate_end_date(cls, v):
        if v and v < dt.datetime.now():
            raise ValueError("End date cannot be in the past.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date.")
        return self
