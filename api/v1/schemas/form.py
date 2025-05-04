import datetime
from enum import Enum
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, EmailStr


class FieldTypeEnum(str, Enum):
    TEXT = 'text'
    NUMBER = 'number'
    TEXTAREA = 'textarea'
    SELECT = 'select'
    EMAIL = 'email'
    CHECKBOX = 'checkbox'
    RADIO = 'radio'
    DATE = 'date'
    TIME = 'time'
    DATETIME_LOCAL = 'datetime-local'
    FILE = 'file'
    URL = 'url'
    TEL = 'tel'
    RANGE = 'range'
    COLOR = 'color'
    

class FormResponseStatus(str, Enum):
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    

FIELD_TYPE_TO_DATA_TYPE_MAPPING = {
    FieldTypeEnum.TEXT: str,
    FieldTypeEnum.NUMBER: float,
    FieldTypeEnum.TEXTAREA: str,
    FieldTypeEnum.SELECT: str,
    FieldTypeEnum.EMAIL: str,
    FieldTypeEnum.CHECKBOX: bool,
    FieldTypeEnum.RADIO: str,
    FieldTypeEnum.DATE: datetime.date,
    FieldTypeEnum.TIME: datetime.time,
    FieldTypeEnum.DATETIME_LOCAL: datetime.datetime,
    FieldTypeEnum.FILE: bytes,  # or UploadFile if FastAPI
    FieldTypeEnum.URL: str,
    FieldTypeEnum.TEL: str,
    FieldTypeEnum.RANGE: float,
    FieldTypeEnum.COLOR: str,  # usually a HEX string like '#ffffff'
}


class FormField(BaseModel):
    label: str                      # Visible label for the field
    name: str                       # 'name' attribute in HTML
    type: Literal[
        "text", "textarea", "email", "number", "password", "tel", "url",
        "search", "date", "time", "datetime-local", "checkbox", "radio",
        "file", "range", "color", "hidden", "select"
    ] = "text"

    required: bool = False
    placeholder: Optional[str] = None
    default: Optional[Any] = None
    readonly: Optional[bool] = False
    disabled: Optional[bool] = False
    autofocus: Optional[bool] = False

    # For inputs like number, range, date, time
    min: Optional[str] = None
    max: Optional[str] = None
    step: Optional[float] = None

    # For string-based inputs
    pattern: Optional[str] = None
    minlength: Optional[int] = None
    maxlength: Optional[int] = None

    # For file inputs
    accept: Optional[str] = None       # e.g. ".jpg,.png,.pdf"
    multiple: Optional[bool] = None    # For file and select inputs

    # For radio, checkbox, select
    options: Optional[List[str]] = None

class FormFieldResponse(BaseModel):
    label: str
    type: Literal[
        "text", "textarea", "email", "number", "password", "tel", "url",
        "search", "date", "time", "datetime-local", "checkbox", "radio",
        "file", "range", "color", "hidden", "select"
    ] = "text"
    response: Any


class FormTemplateBase(BaseModel):
    unique_id: Optional[str] = None
    organization_id: str
    template_name: str
    purpose: str
    fields: List[FormField]
    tag_ids: Optional[List[str]] = []
    
    
class UpdateFormTemplate(BaseModel):
    template_name: Optional[str] = None
    purpose: Optional[str] = None
    fields: Optional[List[FormField]] = None
    tag_ids: Optional[List[str]] = None
    

class FormBase(BaseModel):
    unique_id: Optional[str] = None
    form_template_id: Optional[str] = None
    organization_id: str
    form_name: str
    slug: Optional[str] = None
    url: Optional[str] = None
    purpose: str
    fields: Optional[List[FormField]] = None
    is_active: Optional[bool] = True
    receive_response_email_notifications: Optional[bool] = False
    allow_more_than_one_user_submission: Optional[bool] = True
    

class UpdateForm(BaseModel):
    form_name: Optional[str] = None
    purpose: Optional[str] = None
    fields: Optional[List[FormField]] = None
    form_template_id: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    receive_response_email_notifications: Optional[bool] = None
    allow_more_than_one_user_submission: Optional[bool] = None


class FormResponseBase(BaseModel):
    form_id: str
    email: EmailStr
    status: str = FormResponseStatus.DRAFT.value
    data: List[FormFieldResponse]
    send_email_to_respondent: Optional[bool] = False
    
    
class UpdateFormResponse(BaseModel):
    email: Optional[EmailStr] = None
    status: Optional[str] = None
    data: Optional[List[FormFieldResponse]] = None
    send_email_to_respondent: Optional[bool] = None
