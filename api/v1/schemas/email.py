from datetime import datetime
import enum
from fastapi import File, Form, UploadFile
from pydantic import BaseModel
from typing import List, Optional


class EmailStatus(str, enum.Enum):
    SUCCESS = "success"
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    

class EmailBase(BaseModel):

    unique_id: Optional[str] = None
    
    organization_id: Optional[str] = Form(...),
    
    recipients: str = Form(..., description="Comma separated list of recipient emails"),
    subject: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    footer: Optional[str] = Form(None),

    status: Optional[EmailStatus] = Form(EmailStatus.PENDING),
    priority: Optional[int] = Form(1),
    retries: Optional[int] = Form(0),
    date_sent: Optional[datetime] = Form(None),

    context: Optional[str] = Form(None),  # JSON as string, to be parsed manually
    template_id: Optional[str] = Form(None),
    layout_id: Optional[str] = Form(None),

    attachments: Optional[List[UploadFile]] = File(None)


class UpdateEmail(BaseModel):
    
    recipients: str = Form(None, description="Comma separated list of recipient emails"),
    subject: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    footer: Optional[str] = Form(None),

    status: Optional[EmailStatus] = Form(None),
    priority: Optional[int] = Form(None),
    retries: Optional[int] = Form(None),
    date_sent: Optional[datetime] = Form(None),

    context: Optional[str] = Form(None),  # JSON as string, to be parsed manually
    template_id: Optional[str] = Form(None),
    layout_id: Optional[str] = Form(None),

    attachments: Optional[List[UploadFile]] = File(None)


