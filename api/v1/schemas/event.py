from pydantic import BaseModel
from typing import Optional


class EventBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateEvent(BaseModel):

    unique_id: Optional[str] = None


