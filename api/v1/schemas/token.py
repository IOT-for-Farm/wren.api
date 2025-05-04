from typing import Optional
from pydantic import BaseModel


class TokenData(BaseModel):

    user_id: Optional[str]
