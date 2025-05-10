from celery import Celery, shared_task
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from datetime import datetime
from sqlalchemy.orm import Session
import asyncio

from api.db.database import SessionLocal
from api.utils.language_codes import LANGUAGE_CODES
from api.utils.telex_notification import TelexNotification
from api.v1.models.content import Content, ContentTranslation
from config import config
from api.utils import helpers


BROKER_HOST_PORT = config('RABBITMQ_HOST_PORT')
USER = config('RABBITMQ_USERNAME')
PASS = config('RABBITMQ_PASSWORD')
ENV = config('PYTHON_ENV')

TASK_QUEUES = { 
    'general': f'{ENV}_wren_general', 
    'telex': f'{ENV}_wren_telex_notifications', 
    'email': f'{ENV}_wren_emails', 
    # 'sms': f'{ENV}_wren_sms', 
    # 'import': f'{ENV}_wren_imports', 
    # 'report': f'{ENV}_wren_reports',
    # 'data_indexing': f'{ENV}_wren_data_indexing',
    # 'reminder': f'{ENV}_wren_reminder'
}

# celery -A api.core.dependencies.celery.worker worker -E --logfile=logs/celery.log --loglevel=INFO -Q dev_wren_telex_notifications
# celery -A api.core.dependencies.celery.worker beat -E --logfile=logs/celerybeat.log --loglevel=INFO

beat_schedule = {
    'auto-publish-and-expire-content-every-minute': {
        'task': 'api.core.dependencies.celery.worker.auto_publish_and_expire_content',
        'schedule': crontab(minute='*/1'),  # every 1 minute
    },
}

celery_app = Celery(__name__)
celery_app.conf.broker_url = f"amqp://{USER}:{PASS}@{BROKER_HOST_PORT}/"
celery_app.conf.task_serializer = "pickle" 
celery_app.conf.accept_content = ["pickle"]  
celery_app.conf.result_serializer = "pickle"
celery_app.conf.beat_schedule = beat_schedule

task_logger = get_task_logger(__name__)

# typesense_client = TypesenseClient()

celery_app.autodiscover_tasks()

@celery_app.task(name='worker.send_telex_notification', queue=TASK_QUEUES['telex'])
def send_telex_notification(
    webhook_id: str,
    event_name: str,
    message: str,
    status: str,
    username: str
):
    """
    Celery task to send Telex notifications.
    """
    
    task_logger.info("Telex notifications task started.")
    
    try:
        telex_notification = TelexNotification(webhook_id=webhook_id)
        telex_notification.send_notification(
            event_name=event_name,
            message=message,
            status=status,
            username=username
        )
        task_logger.info("Telex notifications sent successfully.")
        
    except Exception as e:
        task_logger.error(f"Error sending Telex notification: {e}")
        raise e
    
    finally:
        # Optionally, you can add any cleanup code here
        pass


@celery_app.task
def auto_publish_and_expire_content():
    
    db: Session = SessionLocal()
    now = datetime.now()

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


@celery_app.task(name='worker.generate_content_translations', queue=TASK_QUEUES['general'])
def generate_content_translations(content: dict):
    
    db: Session = SessionLocal()
    
    for code in LANGUAGE_CODES:
        task_logger.info(f'Starting transation for `{code}`')

        translated_title = asyncio.run(helpers.translate_text(content['title'], code))
        translated_body = asyncio.run(helpers.translate_text(content['body'], code))
        
        task_logger.info(f'Translation complete for `{code}`')
        
        # Check if translation already exists for that content
        existing_translation = ContentTranslation.fetch_one_by_field(
            db=db, throw_error=False,
            content_id=content['id'],
            language_code=code
        )
        
        if existing_translation:
            existing_translation.title = translated_title
            existing_translation.body = translated_body
            
            db.commit()
            db.refresh(existing_translation)
            
            task_logger.info(f'Translation for content {content["title"]} with langauge code `{code}` updated')
            
        else:             
            # Create content translation
            ContentTranslation.create(
                db=db,
                content_id=content['id'],
                language_code=code,
                title=translated_title,
                body=translated_body
            )
            
            task_logger.info(f'Translation for content {content["title"]} with langauge code `{code}` saved to the database')
