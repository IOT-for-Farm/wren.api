from datetime import datetime
from api.core.dependencies.celery.worker import celery_app, TASK_QUEUES, task_logger
from api.db.database import get_db_with_ctx_manager
from api.v1.models.content import Content


@celery_app.task
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