import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from dateutil.rrule import rrulestr
from datetime import datetime, timezone

from api.core.base.base_model import BaseTableModel
from api.db.database import get_db_with_ctx_manager
from api.v1.schemas.event import AttendeeStatus



class Event(BaseTableModel):
    __tablename__ = 'events'

    organization_id = sa.Column(
        sa.String, sa.ForeignKey("organizations.id"), 
        index=True, nullable=False
    )
    title = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    slug = sa.Column(sa.String, unique=True, index=True)

    visibility = sa.Column(sa.String, index=True)
    event_type = sa.Column(sa.String, nullable=True, index=True)
    
    start = sa.Column(sa.DateTime, nullable=False)
    end = sa.Column(sa.DateTime, nullable=False)
    location = sa.Column(sa.String, nullable=True)  # e.g., Zoom link or room number
    location_type = sa.Column(sa.String, default="virtual")  # or "physical"
    
    allow_rsvp = sa.Column(sa.Boolean, default=False, index=True)
    attendee_limit = sa.Column(sa.Integer)
    
    is_recurring = sa.Column(sa.Boolean, default=False)
    recurrence_rule = sa.Column(sa.String, nullable=True)  # e.g., "FREQ=WEEKLY;BYDAY=MO"

    creator_id = sa.Column(sa.String, sa.ForeignKey("users.id"), index=True)
    additional_info = sa.Column(sa.JSON, default={})

    organization = relationship('Organization')
    creator = relationship(
        "User", 
        backref='created_events', 
        uselist=False, 
        lazy='selectin',
        viewonly=True
    )
    attachments = relationship(
        'File',
        primaryjoin='and_(Event.id==foreign(File.model_id), File.is_deleted==False, File.organization_id==Event.organization_id)',
        lazy='selectin',
        backref='events',
        viewonly=True
    )

    # @hybrid_property
    @hybrid_method
    def event_occurences(self, no_of_occurences: int=10):
        if self.is_recurring and self.recurrence_rule:
            no_of_occurences = min(no_of_occurences, 20)
            
            # Ensure all datetime values are timezone-aware in UTC
            dtstart = self.start.astimezone(timezone.utc)
            
            # rule = rrulestr(self.recurrence_rule, dtstart=dtstart)
            rule = rrulestr(self.recurrence_rule)
            result = list(rule.between(
                after=dtstart, 
                # before=end_date or self.end or datetime(datetime.now().year, 12, 31),
                # before=self.end or datetime(datetime.now().year, 12, 31),
                before=datetime(datetime.now().year, 12, 31, tzinfo=timezone.utc),
                inc=True,  # includes start and end date if they are recurrences as well
                count=no_of_occurences  # limit number of occurences
            ))
            
            return result
        else:
            return []
        
    
    @hybrid_property
    def attendee_count(self):
        with get_db_with_ctx_manager() as db:
            _, _, count = EventAttendee.fetch_by_field(
                db=db, 
                paginate=False,
                event_id=self.id,
                status=AttendeeStatus.ACCEPTED.value
            )
            
            return count
        
    
    @hybrid_property
    def remaining_slots(self):
        return self.attendee_limit - self.attendee_count
    
    
    @hybrid_property
    def is_event_full(self):
        if not self.attendee_limit:
            return False
        
        return self.attendee_count >= self.attendee_limit
        
    
    def to_dict(self, excludes=[], no_of_occurences: int=10):
        return {
            "event_occurences": self.event_occurences(no_of_occurences=no_of_occurences),
            "attendee_count": self.attendee_count,
            "remaining_slots": self.remaining_slots,
            "is_event_full": self.is_event_full,
            **super().to_dict(excludes)
        }

class EventAttendee(BaseTableModel):
    __tablename__ = "event_attendees"    

    event_id = sa.Column(sa.String, sa.ForeignKey("events.id"), nullable=False, index=True)
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"), nullable=True, index=True)  # internal
    email = sa.Column(sa.String, nullable=True)  # external
    name = sa.Column(sa.String, nullable=True)  # for external guests
    phone = sa.Column(sa.String, nullable=True)  # for external guests
    phone_country_code = sa.Column(sa.String, nullable=True)  # for external guests

    status = sa.Column(sa.String, default="invited", index=True)  # invited, accepted, declined
    respnded_at = sa.Column(sa.DateTime, nullable=True)

    event = relationship("Event", backref="attendees", lazy="selectin")
    # user = relationship("User", backref="user_events", lazy="selectin")


class EventReminder(BaseTableModel):
    __tablename__ = "event_reminders"

    event_id = sa.Column(sa.String, sa.ForeignKey("events.id"), nullable=False, index=True)
    # reminder_time = sa.Column(sa.Interval)  # e.g., timedelta(hours=1)
    reminder_interval_minutes = sa.Column(sa.DateTime)  # e.g.,60. Would be used like this: timedelta(minutes=reminder_interval_minutes)
    method = sa.Column(sa.String, default="email", index=True)  # email, sms, in-app
