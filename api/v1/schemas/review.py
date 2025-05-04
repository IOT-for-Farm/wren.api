from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ReviewBase(BaseModel):

    model_name: str
    model_id: str
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    email: str
    name: str
    comment: str
    star_rating: int = Field(default=1, lt=1, gt=5)


class UpdateReview(BaseModel):

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    comment: Optional[str] = None
    star_rating: Optional[int] = Field(default=None, lt=1, gt=5)
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None
