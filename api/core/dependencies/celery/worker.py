from celery import Celery
from celery.utils.log import get_task_logger
from celery.schedules import crontab

from api.utils.telex_notification import TelexNotification
from config import config


BROKER_HOST_PORT = config('RABBITMQ_HOST_PORT')
USER = config('RABBITMQ_USERNAME')
PASS = config('RABBITMQ_PASSWORD')
ENV = config('PYTHON_ENV')

TASK_QUEUES = { 
    'telex': f'{ENV}_wren_telex_notifications', 
    'email': f'{ENV}_wren_emails', 
    # 'sms': f'{ENV}_wren_sms', 
    # 'import': f'{ENV}_wren_imports', 
    # 'report': f'{ENV}_wren_reports',
    # 'data_indexing': f'{ENV}_wren_data_indexing',
    # 'reminder': f'{ENV}_wren_reminder'
}

# celery -A api.core.dependencies.celery.worker worker -E --logfile=logs/celery.log --loglevel=INFO -Q dev_wren_telex_notifications

celery = Celery(__name__)
celery.conf.broker_url = f"amqp://{USER}:{PASS}@{BROKER_HOST_PORT}/"
celery.conf.task_serializer = "pickle" 
celery.conf.accept_content = ["pickle"]  
celery.conf.result_serializer = "pickle"

task_logger = get_task_logger(__name__)

# typesense_client = TypesenseClient()

celery.autodiscover_tasks()


@celery.task(name='worker.send_telex_notification', queue=TASK_QUEUES['telex'])
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
    
    

# @celery.task(name='worker.send_telex_notification', queue=TASK_QUEUES['telex'])
# def send_telex_notification(
#     webhook_id: str,
#     event_name: str,
#     message: str,
#     status: str,
#     username: str
# ):
#     """
#     Celery task to bulk upload files.
#     """
    
#     task_logger.info("Telex notifications task started.")
    
#     try:
#         telex_notification = TelexNotification(webhook_id=webhook_id)
#         telex_notification.send_notification(
#             event_name=event_name,
#             message=message,
#             status=status,
#             username=username
#         )
#         task_logger.info("Telex notifications sent successfully.")
        
#     except Exception as e:
#         task_logger.error(f"Error sending Telex notification: {e}")
#         raise e
    
#     finally:
#         # Optionally, you can add any cleanup code here
#         pass
