from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime

from api.utils.html_sanitizer import sanitize_html


class TemplateBase(BaseModel):
    name: str
    body: str
    organization_id: str
    subject: Optional[str] = None
    image_url: Optional[str] = None
    footer: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True
    layout_id: Optional[str] = None
    feature: Optional[str] = None

    @field_validator("name", "feature", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else v
    
    # @field_validator("body", mode="before")
    # @classmethod
    # def sanitize_html_body(cls, v: str) -> str:
    #     return sanitize_html(v)
    
    @field_validator("subject", "footer", "description", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v


class CreateTemplate(TemplateBase):
    tag_ids: Optional[List[str]] = []


class UpdateTemplate(BaseModel):
    name: Optional[str] = None
    body: Optional[str] = None
    subject: Optional[str] = None
    image_url: Optional[str] = None
    footer: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    layout_id: Optional[str] = None
    feature: Optional[str] = None
    tag_ids: Optional[List[str]] = None
    
    @field_validator("name", "subject", "footer", "description", "feature", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v

    # @field_validator("body", mode="before")
    # @classmethod
    # def sanitize_html_body(cls, v: Optional[str]) -> Optional[str]:
    #     return sanitize_html(v) if v else v
    

class RenderTemplate(BaseModel):
    context: dict


class SendEmail(RenderTemplate):
    recipients: List[EmailStr]