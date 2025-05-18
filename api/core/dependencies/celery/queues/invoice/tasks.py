from datetime import datetime
import time
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.core.dependencies.celery.worker import celery_app, TASK_QUEUES, task_logger
from api.utils.batch_process_query import batch_process_query
from api.v1.models.business_partner import BusinessPartner
from api.v1.services.invoice import InvoiceService


@celery_app.task(name='worker.generate_all_vendor_invoices', queue=TASK_QUEUES['invoice'])
def generate_invoice_for_vendors(
    db: Session,
    organization_id: str,
    vendor_ids: Optional[List[str]] = None,
    due_date: datetime = None,
    year_to_generate_for: int = None,
    month_to_generate_for: int = None,
    send_notification: bool = False,
    currency_code: str = 'NGN',
    template_id: str = None,
    context: dict = None,
):
    
    # Get vendor business partners
    if vendor_ids:
        query = db.query(BusinessPartner).filter(
            BusinessPartner.organization_id==organization_id,
            BusinessPartner.partner_type=='vendor',
        ).filter(
            BusinessPartner.id.in_(vendor_ids)
        )
        
    else:
        query, vendors, count = BusinessPartner.fetch_by_field(
            db=db,
            organization_id=organization_id,
            partner_type='vendor'
        )
    
    task_logger.info(f'Generating invoice for {count} vendor(s)')
    
    start_time = time.perf_counter()
    
    # for vendor in vendors:
    for vendor in batch_process_query(db=db, model=BusinessPartner, query=query, batch_size=10):
        task_logger.info(f'Generating invoice for {vendor.id}- {vendor.company_name}')
        
        try:
            InvoiceService.generate_vendor_invoice(
                db=db,
                organization_id=organization_id,
                vendor_id=vendor.id,
                due_date=due_date,
                year_to_generate_for=year_to_generate_for,
                month_to_generate_for=month_to_generate_for,
                send_notification=send_notification,
                currency_code=currency_code,
                template_id=template_id,
                context=context
            )
            
        except HTTPException as http_exc:
            task_logger.info(http_exc)
            continue
        
        except Exception as e:
            task_logger.info(e)
            raise e
        
        task_logger.info(f'Invoice generated for vendor successfully')
    
    process_time = time.perf_counter() - start_time    
    task_logger.info(f'Total time taken to generate invoices: {process_time/60} minutes')
