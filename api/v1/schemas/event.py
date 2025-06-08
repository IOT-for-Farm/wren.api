from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, model_validator, validator
from typing import List, Optional
from enum import Enum

from api.v1.schemas.base import AdditionalInfoSchema


class EventTypeEnum(str, Enum):
    MEETING = "meeting"
    TRAINING = "training"
    WEBINAR = "webinar"
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    INTERVIEW = "interview"
    DEADLINE = "deadline"
    ANNOUNCEMENT = "announcement"
    TOWNHALL = "townhall"
    PRODUCT_LAUNCH = "product_launch"
    HOLIDAY = "holiday"
    TEAM_BUILDING = "team_building"
    OTHER = "other"


class EventVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    ORGANIZATION_ONLY = "organization_only"
    

class AttendeeStatus(str, Enum):
    INVITED = 'invited'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'


class ReminderMethod(str, Enum):
    SMS = 'sms'
    EMAIL = 'email'
    IN_APP = 'in app'


class LocationType(str, Enum):
    PHYSICAL = 'physical'
    VIRTUAL = 'virtual'

# ==========================================================  
# ==========================================================  

class FrequencyEnum(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class WeekDayEnum(str, Enum):
    MONDAY = "MO"
    TUESDAY = "TU"
    WEDNESDAY = "WE"
    THURSDAY = "TH"
    FRIDAY = "FR"
    SATURDAY = "SA"
    SUNDAY = "SU"


class RecurrenceRuleSchema(BaseModel):
    frequency: FrequencyEnum
    interval: int = 1
    weekday: Optional[List[WeekDayEnum]] = None
    day_of_the_month: Optional[List[int]] = None
    month_integer: Optional[List[int]] = None
    number_of_occurences: Optional[int] = None
    end_date: Optional[datetime] = None

    @validator('day_of_the_month', each_item=True)
    def validate_month_days(cls, v):
        if not (1 <= v <= 31):
            raise ValueError("Month days must be between 1 and 31")
        return v

    @validator('month_integer', each_item=True)
    def validate_months(cls, v):
        if not (1 <= v <= 12):
            raise ValueError("Months must be between 1 and 12")
        
        if v < datetime.now().month:
            raise ValueError('Months cannot be lower than the current month')
        
        return v

    # @classmethod
    def to_rrule(self) -> str:
        parts = [f"FREQ={self.frequency.value}"]

        if self.interval:
            parts.append(f"INTERVAL={self.interval}")
        if self.weekday:
            parts.append(f"BYDAY={','.join(self.weekday)}")
        if self.day_of_the_month:
            parts.append(f"BYMONTHDAY={','.join(map(str, self.day_of_the_month))}")
        if self.month_integer:
            parts.append(f"BYMONTH={','.join(map(str, self.month_integer))}")
        if self.number_of_occurences:
            parts.append(f"COUNT={self.number_of_occurences}")
        if self.end_date:
            parts.append(f"UNTIL={self.end_date.replace(tzinfo=None).strftime('%Y%m%dT%H%M%SZ')}")  # UTC format

        return ";".join(parts)

# =============================================================================
# =============================================================================

class EventBase(BaseModel):

    unique_id: Optional[str] = None
    slug: Optional[str] = None
    
    organization_id: str
    title: str
    description: Optional[str] = None
    visibility: EventVisibility
    event_type: Optional[EventTypeEnum] = None
    start: datetime
    end: datetime
    location: Optional[str] = None
    location_type: Optional[LocationType] = LocationType.VIRTUAL
    allow_rsvp: Optional[bool] = False
    attendee_limit: Optional[int] = None
    is_recurring: Optional[bool] = False
    recurrence_rule: Optional[RecurrenceRuleSchema] = None
    
    tag_ids: Optional[List[str]] = []
    additional_info: Optional[List[AdditionalInfoSchema]] = None
    
    @field_validator("start")
    def validate_start(cls, v):
        if v and v < datetime.now():
            raise ValueError("Start date cannot be in the past.")
        return v

    @field_validator("end")
    def validate_end(cls, v):
        if v and v < datetime.now():
            raise ValueError("End date cannot be in the past.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start and self.end:
            if self.end < self.start:
                raise ValueError("End date cannot be before start date.")
        
        if self.is_recurring and not self.recurrence_rule:
            raise ValueError('Recurrence rule must be provided if event will be a recurring event')
        
        if not self.is_recurring and self.recurrence_rule:
            raise ValueError('The event must be set as a recurring event if recurrence rule id provided')
        
        return self


class UpdateEvent(BaseModel):

    title: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[EventVisibility] = None
    event_type: Optional[EventTypeEnum] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    location: Optional[str] = None
    location_type: Optional[LocationType] = None
    allow_rsvp: Optional[bool] = None
    attendee_limit: Optional[int] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[RecurrenceRuleSchema] = None
    
    tag_ids: Optional[List[str]] = None
    additional_info: Optional[List[AdditionalInfoSchema]] = None
    additional_info_keys_to_remove: Optional[List[str]] = None
    
    @field_validator("start")
    def validate_start(cls, v):
        if v and v < datetime.now():
            raise ValueError("Start date cannot be in the past.")
        return v

    @field_validator("end")
    def validate_end(cls, v):
        if v and v < datetime.now():
            raise ValueError("End date cannot be in the past.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start and self.end:
            if self.end < self.start:
                raise ValueError("End date cannot be before start date.")
        
        return self


class InviteUser(BaseModel):
    user_ids: Optional[List[str]] = None
    emails: Optional[List[EmailStr]] = None
    template_id: Optional[str] = None
    context: Optional[dict] = None
    
    # @classmethod
    @model_validator(mode='after')
    def validate_event_attendee(self):
        if not self.user_ids and not self.emails:
            raise ValueError('Both user ids and emails cannot be empty')
        
        if self.user_ids and self.emails:
            raise ValueError('Both user ids and emails cannot be present at the same time')

        return self

class EventAttendeeBase(BaseModel):
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    phone_country_code: Optional[str] = None
    status: Optional[AttendeeStatus] = AttendeeStatus.INVITED
    
    # @classmethod
    @model_validator(mode='after')
    def validate_event_attendee(self):
        if not all([self.user_id, self.email, self.name, self.phone, self.phone_country_code]):
            raise ValueError('Both user id and all relevant contact information cannot be empty')
        
        if self.user_id and any([self.email, self.name]):
            raise ValueError('Name and email not required as user id is provided')
        
        if self.phone and not self.phone_country_code:
            raise ValueError('Phone country code is required')
        
        if not self.phone and self.phone_country_code:
            raise ValueError('Phone is required')

        return self


class AddAttendeeToEvent(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    phone_country_code: Optional[str] = None
    
    # @classmethod
    @model_validator(mode='after')
    def validate_event_attendee(self):
        if self.phone and not self.phone_country_code:
            raise ValueError('Phone country code is required')
        
        if not self.phone and self.phone_country_code:
            raise ValueError('Phone is required')

        return self
    
class EventAttendeeUpdate(BaseModel):
    status: Optional[AttendeeStatus] = None


class EventReminderBase(BaseModel):
    reminder_interval_minutes: int = 60
    method: ReminderMethod = ReminderMethod.EMAIL
    

class UpdateEventReminder(BaseModel):
    reminder_interval_minutes: Optional[int] = None
    method: Optional[ReminderMethod] = None
