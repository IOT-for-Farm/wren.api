from pydantic import BaseModel
from typing import Optional


class CommentBase(BaseModel):

    model_name: str
    model_id: str
    parent_id: Optional[str] = None
    
    email: Optional[str] = None
    name: Optional[str] = None
    text: str
    

class UpdateComment(BaseModel):
    
    email: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None
