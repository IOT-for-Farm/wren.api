from typing import Optional
from pydantic import BaseModel

from api.v1.schemas.auth import UserType


class TokenData(BaseModel):

    user_id: Optional[str]
    user_type: Optional[str] = UserType.user.value
