import asyncio

from api.db.database import get_db_with_ctx_manager
from api.utils.language_codes import LANGUAGE_CODES
from api.utils.telex_notification import TelexNotification
from api.v1.models.content import Content, ContentTranslation
from api.utils import helpers
from api.utils.batch_process_query import batch_process_query


from api.core.dependencies.celery.worker import celery_app, TASK_QUEUES, task_logger


@celery_app.task(name='worker.send_telex_notification', queue=TASK_QUEUES['general'])
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
    

@celery_app.task(name='worker.generate_content_translations', queue=TASK_QUEUES['general'])
def generate_content_translations(content: dict):
        
    with get_db_with_ctx_manager() as db:
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
