from pydantic import BaseModel
from typing import Optional


class CategoryBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateCategory(BaseModel):

    unique_id: Optional[str] = None


