from pydantic import BaseModel, field_validator
from typing import Optional

from api.utils.html_sanitizer import sanitize_html


class LayoutBase(BaseModel):
    organization_id: str
    name: str
    layout: str
    feature: Optional[str] = None

    @field_validator("name", "feature", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v

    # @field_validator("layout")
    # @classmethod
    # def clean_html(cls, v: str) -> str:
    #     return sanitize_html(v)
    

class UpdateLayout(BaseModel):
    name: Optional[str] = None
    layout: Optional[str] = None
    feature: Optional[str] = None

    @field_validator("name", "feature", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v

    # @field_validator("layout")
    # @classmethod
    # def clean_html(cls, v: str) -> str:
    #     return sanitize_html(v)
