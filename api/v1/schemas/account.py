from pydantic import BaseModel
from typing import Optional


class AccountBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateAccount(BaseModel):

    unique_id: Optional[str] = None


