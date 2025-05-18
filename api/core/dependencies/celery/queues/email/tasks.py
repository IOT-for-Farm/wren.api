import asyncio
from typing import List, Optional
from api.core.dependencies.celery.worker import celery_app, TASK_QUEUES, task_logger
from api.core.dependencies.email_sending_service import send_email


@celery_app.task(name='worker.send_email', queue=TASK_QUEUES['email'])
def send_email_celery(
    recipients: List[str], 
    subject: str, 
    template_name: Optional[str]=None, 
    html_template_string: Optional[str]=None, 
    attachments: Optional[List[str]]=None,
    template_data: Optional[dict] = {},
    apply_default_template_data: bool = True,
    add_pdf_attachment: bool = False
):
    
    task_logger.info(f'Sending mail fro celery to: {recipients}')
    
    asyncio.run(send_email(
        recipients=recipients,
        subject=subject,
        template_name=template_name,
        html_template_string=html_template_string,
        attachments=attachments,
        template_data=template_data,
        apply_default_template_data=apply_default_template_data,
        add_pdf_attachment=add_pdf_attachment,
    ))
    
    task_logger.info('Email sent successfully')
