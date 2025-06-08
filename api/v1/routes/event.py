from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from slugify import slugify
from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.organization import OrganizationMember
from api.v1.models.tag import TagAssociation, Tag
from api.v1.models.user import User
from api.v1.models.event import Event, EventAttendee, EventReminder
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.event import EventService
from api.v1.schemas import event as event_schemas
from api.utils.loggers import create_logger
from api.v1.services.tag import TagService


event_router = APIRouter(prefix='/events', tags=['Event'])
logger = create_logger(__name__)

@event_router.post("", status_code=201, response_model=success_response)
async def create_event(
    payload: event_schemas.EventBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new event"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='event:create',
        organization_id=payload.organization_id
    )
    
    if not payload.slug:
        payload.slug = slugify(payload.title)
        
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )
        
    if payload.additional_info:
        payload.additional_info = helpers.format_additional_info_create(payload.additional_info)

    event = Event.create(
        db=db,
        creator_id=entity.entity.id,
        recurrence_rule=(
            payload.recurrence_rule.to_rrule() 
            if payload.recurrence_rule
            else None
        ),
        **payload.model_dump(
            exclude_unset=True, 
            exclude=['tag_ids', 'recurrence_rule']
        )
    )
    
    # Add user to event attendees
    EventAttendee.create(
        db=db,
        event_id=event.id,
        user_id=event.creator_id,
        email=event.creator.email,
        phone=event.creator.phone_number,
        phone_country_code=event.creator.phone_country_code,
        name=f'{event.creator.first_name} {event.creator.last_name}',
        status=event_schemas.AttendeeStatus.ACCEPTED.value
    )
    
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=payload.organization_id,
            model_type='events',
            entity_id=event.id
        )

    logger.info(f'Event with id {event.id} created')

    return success_response(
        message=f"Event created successfully",
        status_code=201,
        data=event.to_dict()
    )


@event_router.get("", status_code=200)
async def get_events(
    organization_id: str,
    title: str = None,
    slug: str = None,
    tags: str = None,
    visibility: str = None,
    event_type: str = None,
    location_type: str = None,
    start: datetime = None,
    end: datetime = None,
    no_of_occurences: int = 10,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all events"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, events, count = Event.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'title': title,
        },
        organization_id=organization_id,
        slug=slug,
        visibility=visibility,
        event_type=event_type,
        location_type=location_type,
    )
    
    if start and not end:
        query = query.filter(Event.start >= start)
    
    if end and not start:
        query = query.filter(Event.end >= end)
        
    if start and end:
        query = query.filter(
            and_(
                Event.end <= end,
                Event.start >= start,
            )
        )
    
    if tags:
        tags_list = [tag.strip() for tag in tags.split(',')]      
        query = (
            query
            .join(TagAssociation, TagAssociation.entity_id==Event.id)
            .join(Tag, Tag.id == TagAssociation.tag_id)
            .filter(Tag.name.in_(tags_list))
        )
        
    events, count = paginator.paginate_query(query, page, per_page)
    
    return paginator.build_paginated_response(
        items=[
            event.to_dict(no_of_occurences=no_of_occurences) 
            for event in events
        ],
        endpoint='/events',
        page=page,
        size=per_page,
        total=count,
    )


@event_router.get("/{id}", status_code=200, response_model=success_response)
async def get_event_by_id(
    id: str,
    organization_id: str,
    no_of_occurences: int = 20,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a event by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    event = Event.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched event successfully",
        status_code=200,
        data=event.to_dict(no_of_occurences=no_of_occurences)
    )


@event_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_event(
    id: str,
    organization_id: str,
    payload: event_schemas.UpdateEvent,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a event"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='event:update',
        organization_id=organization_id
    )

    previous_event = Event.fetch_by_id(db, id)
    
    event = Event.update(
        db=db,
        id=id,
        recurrence_rule=(
            payload.recurrence_rule.to_rrule() 
            if payload.recurrence_rule
            else previous_event.recurrence_rule
        ),
        **payload.model_dump(exclude_unset=True,exclude=[
            'tag_ids', 
            'additional_info',
            'additional_info_keys_to_remove',
            'recurrence_rule'
        ])
    )
    
    if payload.additional_info:
        event.additional_info = helpers.format_additional_info_update(
            additional_info=payload.additional_info,
            model_instance=event,
            keys_to_remove=payload.additional_info_keys_to_remove
        )
        db.commit()
    
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=organization_id,
            model_type='events',
            entity_id=event.id
        )

    logger.info(f'Event with id {event.id} updated')

    return success_response(
        message=f"Event updated successfully",
        status_code=200,
        data=event.to_dict()
    )


@event_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_event(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a event"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='event:delete',
        organization_id=organization_id
    )

    Event.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )


@event_router.post("/{id}/public-event-register", status_code=200, response_model=success_response)
async def register_for_public_event(
    id: str,
    payload: event_schemas.AddAttendeeToEvent,
    db: Session=Depends(get_db), 
):
    """Endpoint to add a user to event. This is for public events and works like registering for the event"""

    event = Event.fetch_by_id(db, id)
    
    if event.visibility != event_schemas.EventVisibility.PUBLIC.value:
        raise HTTPException(400, 'Cannot join this event')
    
    if event.is_event_full:
        raise HTTPException(400, 'Event is at capacity')
 
    # Check event attendeedif user has been invited
    existing_attendee = EventAttendee.fetch_one_by_field(
        db=db, throw_error=False,
        event_id=event.id,
        email=payload.email,
        status=event_schemas.AttendeeStatus.ACCEPTED.value
    )
    
    if existing_attendee:
        raise HTTPException(400, 'You are already an attendee at this event')
    
    # Create attendee as invited
    attendee = EventAttendee.create(
        db=db,
        status=event_schemas.AttendeeStatus.ACCEPTED.value,
        **payload.model_dump(exclude_unset=True)
    )
        
    # Send email invitation
    EventService.send_event_acceptance_mail(
        db=db, 
        email=payload.email, 
        event_id=event.id,
        attendee_id=attendee.id
    )
    
    return success_response(
        message=f"Successfully registered for event",
        status_code=200
    )


@event_router.post("/{id}/organization-event-register", status_code=200, response_model=success_response)
async def register_for_organization_event(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to add am organization user to an event"""
    
    user: User = entity.entity

    event = Event.fetch_by_id(db, id)
    
    if event.visibility != event_schemas.EventVisibility.ORGANIZATION_ONLY.value:
        raise HTTPException(400, 'Event must be an organization only event')
    
    if event.is_event_full:
        raise HTTPException(400, 'Event is at capacity')
    
    # Check event attendee if they are part of the event
    existing_attendee = EventAttendee.fetch_one_by_field(
        db=db, throw_error=False,
        event_id=event.id,
        user_id=user.id,
        status=event_schemas.AttendeeStatus.ACCEPTED.value
    )
    
    if existing_attendee:
        raise HTTPException(400, 'You are already an attendee at this event')
    
    # Create attendee as invited
    attendee = EventAttendee.create(
        db=db,
        event_id=event.id,
        user_id=user.id,
        name=f'{user.first_name} {user.last_name}',
        email=user.email,
        phone=user.phone_number,
        phone_country_code=user.phone_country_code,
        status=event_schemas.AttendeeStatus.ACCEPTED.value,
    )
        
    # Send email invitation
    EventService.send_event_acceptance_mail(
        db=db, 
        email=user.email, 
        event_id=event.id,
        attendee_id=attendee.id
    )
    
    return success_response(
        message=f"Successfully registered for event",
        status_code=200
    )
    

@event_router.post("/{id}/invite-user", status_code=200, response_model=success_response)
async def invite_user_to_event(
    id: str,
    organization_id: str,
    payload: event_schemas.InviteUser,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to invite a user a event"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='event:invite-user',
        organization_id=organization_id
    )

    event = Event.fetch_by_id(db, id)
    
    if event.visibility == event_schemas.EventVisibility.PUBLIC:
        raise HTTPException(400, 'Cannot invite users to a public event')
    
    if event.is_event_full:
        raise HTTPException(400, 'Event is at capacity')
    
    no_of_invitations_sent = 0
    emails = []
    
    if payload.user_ids:
        if event.attendee_limit and len(payload.user_ids) > event.remaining_slots:
            raise HTTPException(400, f'Cannot invite nore than {event.remaining_slots} users ')
        
        for user_id in payload.user_ids:
            # Check if user is a member of the organization
            user_in_org = OrganizationMember.fetch_one_by_field(
                db=db, thorw_error=False,
                organization_id=organization_id,
                user_id=user_id
            )
            
            if not user_in_org:
                continue
            
            # Check event attendeedif user has been invited
            existing_attendee = EventAttendee.fetch_one_by_field(
                db=db, throw_error=False,
                event_id=event.id,
                user_id=user_id,
                email=email,
                status=event_schemas.AttendeeStatus.INVITED.value
            )
            
            if existing_attendee:
                continue
            
            # Create attendee as invited
            attendee = EventAttendee.create(
                db=db,
                event_id=event.id,
                user_id=user_id,
                email=user_in_org.user.email,
                name=f'{user_in_org.user.first_name} {user_in_org.user.last_name}',
                status=event_schemas.AttendeeStatus.INVITED.value
            )
            
            emails.append(user_in_org.user.email)
            no_of_invitations_sent += 1
    
    if payload.emails:
        emails = payload.emails
        
        if event.attendee_limit and len(payload.emails) > event.remaining_slots:
            raise HTTPException(400, f'Cannot invite nore than {event.remaining_slots} users ')
        
        for email in emails:
            # Check event attendeed if user has been invited
            existing_attendee = EventAttendee.fetch_one_by_field(
                db=db, throw_error=False,
                event_id=event.id,
                email=email,
                status=event_schemas.AttendeeStatus.INVITED.value
            )
            
            if existing_attendee:
                continue
            
            attendee = EventAttendee.create(
                db=db,
                event_id=event.id,
                email=email,
                name=email.split('@')[0],
                status=event_schemas.AttendeeStatus.INVITED.value,
            )
            
            no_of_invitations_sent += 1
    
    # Send email invitation
    EventService.send_invite_mail(
        db=db, 
        emails=emails, 
        event_id=event.id, 
        attendee_id=attendee.id,
        template_id=payload.template_id,
        context=payload.context,
    )
    
    return success_response(
        message=f"{no_of_invitations_sent} invitation(s) sent successfully",
        status_code=200
    )


@event_router.get("/{id}/respond-to-invite", status_code=200, response_model=success_response)
async def respond_to_event_invitation(
    id: str,
    email: EmailStr,
    status: str,  #accepted or declined
    db: Session=Depends(get_db), 
    # entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to invite a user a event"""
    
    if status not in ['accepted', 'declined']:
        raise HTTPException(400, f'Invalid status provided. Expecint accepted or declined. Got {status}')

    event = Event.fetch_by_id(db, id)
    
    attendee = EventAttendee.fetch_one_by_field(
        db=db, throw_error=False,
        event_id=event.id,
        email=email
    )
    
    if attendee.status in ['accepted', 'declined']:
        raise HTTPException(400, 'Invitattion not valid as it has been accepted or declined')
    
    attendee.status = status
    db.commit()
    
    # Send email invitation
    if status == 'accepted':
        EventService.send_event_acceptance_mail(
            db=db, 
            email=email, 
            event_id=event.id,
            attendee_id=attendee.id,
        )
    
    return success_response(
        message=f"Invitation sent successfully",
        status_code=200
    )


@event_router.get("/{id}/attendees", status_code=200)
async def get_event_attendees(
    id: str,
    organization_id: str,
    status: str = None,
    name: str = None,
    email: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all event attendees."""

    event = Event.fetch_by_id(db, id)
    
    query, attendees, count = EventAttendee.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
            'email': email,
        },
        event_id=event.id,
        organization_id=organization_id,
        status=status,
    )
    
    return paginator.build_paginated_response(
        items=[attendee.to_dict() for attendee in attendees],
        endpoint=f'/{id}/attendees',
        page=page,
        size=per_page,
        total=count,
    )


@event_router.post("/{id}/reminders", status_code=201, response_model=success_response)
async def create_event_reminder(
    id: str,
    payload: event_schemas.EventReminderBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create an event reminder"""
    
    event = Event.fetch_by_id(db, id)
    
    event_reminder = EventReminder.create(
        db=db,
        event_id=event.id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Event reminder created successfully",
        status_code=201,
        data=event_reminder.to_dict()
    )


@event_router.patch("/reminders/{id}", status_code=200, response_model=success_response)
async def update_event_reminder(
    id: str,
    payload: event_schemas.UpdateEventReminder,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update an event reminder"""
    
    reminder = EventReminder.fetch_by_id(db, id)
    
    event_reminder = EventReminder.update(
        db=db,
        id=reminder.id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Event reminder updated successfully",
        status_code=200,
        data=event_reminder.to_dict()
    )
    

@event_router.delete("/reminders/{id}", status_code=200, response_model=success_response)
async def delete_event_reminder(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete an event reminder"""
    
    EventReminder.soft_delete(db, id)

    return success_response(
        message=f"Event reminder deleted successfully",
        status_code=200,
    )
