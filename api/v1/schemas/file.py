from typing import Optional
from fastapi import File, Form, UploadFile
from pydantic import BaseModel, field_validator

from api.utils.schema_to_form_converter import as_form


# @as_form
class FileBase(BaseModel):
    
    file: UploadFile = File(...)
    organization_id: str = Form(...)
    file_name: Optional[str] = Form(None)
    model_id: str = Form(...)
    model_name: str = Form(...)
    url: Optional[str] = Form(None)
    description: Optional[str] = Form(None)
    label: Optional[str] = Form(None)
    
    @field_validator( "model_name", "label", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v
    

# @as_form
class UpdateFile(BaseModel):
    
    file: Optional[UploadFile] = File(None)
    file_name: Optional[str] = Form(None)
    url: Optional[str] = Form(None)
    description: Optional[str] = Form(None)
    label: Optional[str] = Form(None)
    
    @field_validator("label", mode="before")
    @classmethod
    def strip_and_lower(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if isinstance(v, str) else v


class FolderBase(BaseModel):

    name: str
    organization_id: str
    parent_id: Optional[str] = None


class UpdateFolder(BaseModel):
    
    name: Optional[str] = None
    parent_id: Optional[str] = None
