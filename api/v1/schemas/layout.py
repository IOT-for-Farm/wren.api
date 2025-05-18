from fastapi import File, Form, UploadFile
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

from api.utils.html_sanitizer import sanitize_html


class LayoutBase(BaseModel):
    organization_id: str = Form(...)
    name: str = Form(...)
    layout: Optional[str] = Form(None)
    feature: Optional[str] = Form(None)
    file: Optional[UploadFile] = File(None)

    @field_validator("name", "feature", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v
    
    @model_validator(mode='after')
    def check_layout_or_file(self) -> 'LayoutBase':
        if self.layout is not None and self.file is not None:
            raise ValueError("Cannot provide both layout and file - choose one")
        
        if self.layout is None and self.file is None:
            raise ValueError("Either layout or file must be provided")
        
        return self

    @field_validator('layout')
    @classmethod
    def validate_layout(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Layout cannot be empty or whitespace only")
        return v.strip() if v is not None else None

    @field_validator('file')
    @classmethod
    def validate_file(cls, v: Optional[UploadFile]) -> Optional[UploadFile]:
        if v is not None and v.size == 0:
            raise ValueError("Uploaded file cannot be empty")
        return v
    
    # @root_validator
    # def check_layout_or_file(cls, values):
    #     layout = values.get('layout')
    #     file = values.get('file')
        
    #     if layout is not None and file is not None:
    #         raise ValueError("Cannot provide both layout and file - choose one")
        
    #     if layout is None and file is None:
    #         raise ValueError("Either layout or file must be provided")
        
    #     return values

    # @validator('layout')
    # def validate_layout(cls, v):
    #     if v is not None and v.strip() == "":
    #         raise ValueError("Layout cannot be empty string")
    #     return v

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
