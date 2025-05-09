from datetime import datetime
import enum
from fastapi import File, Form, UploadFile
from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional

from api.v1.schemas.base import AdditionalInfoSchema


class ProjectStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    on_hold = "on_hold"
    cancelled = "cancelled"
    

class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    

class ProjectMemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class ProjectBase(BaseModel):
    
    unique_id: Optional[str] = Form(None)
    project_image: Optional[UploadFile] = File(None)
    attachments: Optional[List[UploadFile]] = File(None)
    name: str = Form(...)
    slug: Optional[str] = Form(None)
    logo_url: Optional[str] = Form(None)
    description: Optional[str] = Form(None)
    organization_id: Optional[str] = Form(None)
    department_id: Optional[str] = Form(None)
    start_date: Optional[datetime] = Form(default=datetime.now())
    end_date: Optional[datetime] = Form(None)
    status: Optional[ProjectStatus] = Form(ProjectStatus.not_started)
    additional_info: Optional[List[AdditionalInfoSchema]] = None
    
    @field_validator("start_date")
    def validate_start_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Start date cannot be in the past.")
        return v

    @field_validator("end_date")
    def validate_end_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("End date cannot be in the past.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date.")
        return self
    
    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    
    project_image: Optional[UploadFile] = File(None)
    attachments: Optional[List[UploadFile]] = File(None)
    name: Optional[str] = Form(None)
    logo_url: Optional[str] = Form(None)
    description: Optional[str] = Form(None)
    start_date: Optional[datetime] = Form(None)
    end_date: Optional[datetime] = Form(None)
    status: Optional[ProjectStatus] = Form(None)
    additional_info: Optional[List[AdditionalInfoSchema]] = Form(None)
    
    @field_validator("start_date")
    def validate_start_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Start date cannot be in the past.")
        return v

    @field_validator("end_date")
    def validate_end_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("End date cannot be in the past.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date.")
        return self

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    
    attachments: Optional[List[UploadFile]] = File(None)
    unique_id: Optional[str] = Form(None)
    project_id: str = Form(...)
    name: str = Form(...)
    parent_id: Optional[str] = Form(None)
    description: Optional[str] = Form(None)
    priority: Optional[Priority] = Form(Priority.medium)
    status: Optional[ProjectStatus] = Form(ProjectStatus.not_started)
    due_date: Optional[datetime] = Form(None)
    additional_info: Optional[List[AdditionalInfoSchema]] = Form(None)
    
    @field_validator("due_date")
    def validate_due_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date date cannot be in the past.")
        return v

    class Config:
        from_attributes = True


class TaskCreate(TaskBase):
    assignee_ids: Optional[List[str]] = Form(None)


class TaskUpdate(BaseModel):
    
    attachments: Optional[List[UploadFile]] = File(None)
    name: Optional[str] = Form(None)
    parent_id: Optional[str] = Form(None)
    description: Optional[str] = Form(None)
    priority: Optional[Priority] = Form(None)
    status: Optional[ProjectStatus] = Form(None)
    due_date: Optional[datetime] = Form(None)
    assignee_ids: Optional[List[str]] = Form(None)
    additional_info: Optional[List[AdditionalInfoSchema]] = Form(None)
    
    @field_validator("due_date")
    def validate_due_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date date cannot be in the past.")
        return v
    class Config:
        from_attributes = True


class MilestoneBase(BaseModel):
    
    unique_id: Optional[str] = None
    project_id: str
    name: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    
    @field_validator("due_date")
    def validate_due_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date date cannot be in the past.")
        return v
    
    class Config:
        from_attributes = True
        

class MilestoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    
    @field_validator("due_date")
    def validate_due_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date date cannot be in the past.")
        return v

    class Config:
        from_attributes = True


class ProjectMemberBase(BaseModel):
    
    user_id: str
    role: ProjectMemberRole


class UpdateProjectMember(BaseModel):
    
    user_id: str
    role: Optional[ProjectMemberRole] = None
    is_active: Optional[bool] = None
    

class TaskAssigneeBase(BaseModel):
    
    user_id: str
    

class UpdateTaskAssignee(BaseModel):
    
    user_id: str
    is_active: Optional[bool] = None
