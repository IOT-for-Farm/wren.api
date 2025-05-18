from celery import Celery
from celery.utils.log import get_task_logger
from celery.schedules import crontab
from config import config


BROKER_HOST = config('RABBITMQ_HOST')
PORT = config('RABBITMQ_PORT')
USER = config('RABBITMQ_USERNAME')
PASS = config('RABBITMQ_PASSWORD')
ENV = config('PYTHON_ENV')

TASK_QUEUES = { 
    'general': f'{ENV}_wren_general', 
    'email': f'{ENV}_wren_emails', 
    'invoice': f'{ENV}_wren_invoices', 
    # 'data_indexing': f'{ENV}_wren_data_indexing',
    # 'sms': f'{ENV}_wren_sms', 
    # 'import': f'{ENV}_wren_imports', 
    # 'report': f'{ENV}_wren_reports',
    # 'reminder': f'{ENV}_wren_reminder'
}

# celery -A api.core.dependencies.celery.worker worker -E --logfile=logs/celery.log --loglevel=INFO -Q dev_wren_telex_notifications
# celery -A api.core.dependencies.celery.worker beat --logfile=logs/celerybeat.log --loglevel=INFO

SCHEDULED_BASE = 'api.core.dependencies.celery.queues.scheduled_tasks'
beat_schedule = {
    'auto-publish-and-expire-content-every-minute': {
        'task': f'{SCHEDULED_BASE}.auto_publish_and_expire_content',
        'schedule': crontab(minute='*/1'),  # every 1 minute
    },
}

celery_app = Celery(__name__)
celery_app.conf.broker_url = f"amqp://{USER}:{PASS}@{BROKER_HOST}:{PORT}/"
celery_app.conf.task_serializer = "pickle" 
celery_app.conf.accept_content = ["pickle"]  
celery_app.conf.result_serializer = "pickle"
celery_app.conf.beat_schedule = beat_schedule

task_logger = get_task_logger(__name__)

# typesense_client = TypesenseClient()

celery_app.autodiscover_tasks(
    packages=[
        f'api.core.dependencies.celery.queues.{queue}'
        for queue in list(TASK_QUEUES.keys())
    ]
)

# TODO: Write a function that checks through all inventories and takes the ones that have gone below or are approaching
# their reorder threshold and send notification to the vendor or organization or both


# TODO: Write a function that checks all invoices and marks those that have gone
# past the due date as overdue and notify the respective owner of the invoice
