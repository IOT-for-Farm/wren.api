from datetime import datetime, timedelta
from api.core.dependencies.celery.worker import celery_app, TASK_QUEUES, task_logger
from api.db.database import get_db_with_ctx_manager
from api.v1.models.content import Content
from api.v1.models.event import Event, EventAttendee, EventReminder
from api.v1.schemas.event import AttendeeStatus


@celery_app.task(name='worker.auto_publish_and_expire_content', queue=TASK_QUEUES['scheduled'])
def auto_publish_and_expire_content():
    
    now = datetime.now()

    with get_db_with_ctx_manager() as db:
        task_logger.info('Auto publish started')
        # Activate content that is scheduled to be published
        publishable = db.query(Content).filter(
            Content.publish_date <= now,
            Content.review_status == 'approved',
            Content.content_status.in_(['unpublished', 'scheduled'])
        ).all()

        for content in publishable:
            content.content_status = 'published'
        
        task_logger.info('Auto publish completed')
        
        task_logger.info('Auto expiration started')
        # Deactivate content that has expired
        expirable = db.query(Content).filter(
            Content.expiration_date <= now,
            Content.review_status == 'approved',
            Content.content_status == 'published'
        ).all()

        for content in expirable:
            content.content_status = 'expired'
        
        task_logger.info('Auto expiration completed')

        db.commit()
        db.close()
        
        task_logger.info('DB updated')


# TODO: Write a function that checks through all inventories and takes the ones that have gone below or are approaching
# their reorder threshold and send notification to the vendor or organization or both


# TODO: Write a function that checks all invoices and marks those that have gone
# past the due date as overdue and notify the respective owner of the invoice


# TODO: Write function to send reminders for events after reminder interval has been reached
@celery_app.task(name='worker.send_event_remidners', queue=TASK_QUEUES['scheduled'])
def send_event_reminders():
    
    now = datetime.now()
    
    with get_db_with_ctx_manager() as db:
        task_logger.info('Getting due reminders')
        
        query = (
            db.query(EventReminder)
            .join(Event, Event.id == EventReminder.event_id)
            .filter(
                (Event.start - timedelta(minutes=EventReminder.reminder_interval_minutes)) <= now,
                Event.start > now  # ensure it's still upcoming
            )
        )
        reminders_due = query.all()
        
        task_logger.info(f'Number of reminders: {query.count()}')
        
        if query.count() == 0:
            task_logger.info('No reminders to send. Exiting...')
            return
        
        for n, reminder in enumerate(reminders_due):
            task_logger.info(f'Sending reminder {n+1}')
            
            # Get event attendees
            query, attendees, count = EventAttendee.fetch_by_field(
                db=db,
                paginate=False,
                event_id=reminder.event_id,
                status=AttendeeStatus.ACCEPTED.value
            )
            
            # Get emails
            attendee_emails = [attendee.email for attendee in attendees]
            
            task_logger.info('Sending emails')
            task_logger.info(attendee_emails)
            
            # TODO: Send reminder email
            
            task_logger.info('Email sent to attendees')
            
        task_logger.info('All reminders processed')