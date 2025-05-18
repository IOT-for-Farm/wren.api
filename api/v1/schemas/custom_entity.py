from pydantic import BaseModel
from typing import Optional


class Custom_entityBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateCustom_entity(BaseModel):

    unique_id: Optional[str] = None


