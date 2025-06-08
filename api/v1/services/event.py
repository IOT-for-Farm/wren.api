from typing import List
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from api.core.dependencies.celery.queues.email.tasks import send_email_celery
from api.utils.loggers import create_logger
from api.v1.models.event import Event, EventAttendee
from api.v1.schemas import event as event_schemas
from api.v1.services.template import TemplateService


logger = create_logger(__name__)

class EventService:
    
    @classmethod
    def is_event_creator(
        cls, 
        db: Session, 
        event_id: str, 
        current_user_id: str
    ):
        '''Function to check if the current user is the event creator'''
        
        event = Event.fetch_by_id(db, event_id)
        
        if event.creator_id != current_user_id:
            raise HTTPException(400, 'You do not have access to this resource')
        
        return True

    
    @classmethod
    def send_invite_mail(
        cls, 
        db: Session, 
        emails: List[EmailStr], 
        event_id: str,
        attendee_id: str,
        template_id: str = None,
        context: dict = None
    ):
        '''Function to send event invitation mail'''
        
        event = Event.fetch_by_id(db, event_id)
        attendee = EventAttendee.fetch_by_id(db, attendee_id)
        
        for email in emails:
            # TODO: Update the revp_link
            template_data = {
                'event': event.to_dict(),
                'attendee': attendee.to_dict(),
                'rsvp_link': f'http://localhost:7001/api/v1/events/{event.id}?email={email}&status=accepted'
            }
            
            html = None
            if template_id:
                template_data = template_data if not context else context
                
                # Render template to extract html
                html, _, _, _ = TemplateService.render_template(
                    db=db,
                    template_id=template_id,
                    context=template_data
                )
                
            send_email_celery.delay(
                recipients=[email],
                subject='You are Invited!',
                template_name='event-invitation.html' if not template_id else None,
                html_template_string=html if template_id else None,
                template_data=template_data
            )
    
    
    @classmethod
    def send_event_acceptance_mail(
        cls, 
        db: Session, 
        email: EmailStr, 
        event_id: str,
        attendee_id: str,
    ):
        '''Fucntion to send event acceptance email'''

        event = Event.fetch_by_id(db, event_id)
        

