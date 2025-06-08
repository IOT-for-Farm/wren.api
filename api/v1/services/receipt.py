from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from api.core.dependencies.celery.queues.email.tasks import send_email_celery
from api.utils import helpers
from api.utils.loggers import create_logger
from api.v1.models.customer import Customer
from api.v1.models.invoice import Invoice
from api.v1.models.receipt import Receipt
from api.v1.models.vendor import Vendor
from api.v1.schemas import receipt as receipt_schemas
from api.v1.services.sale import SaleService
from api.v1.services.template import TemplateService


logger = create_logger(__name__)

class ReceiptService:
    
    @classmethod
    def generate_receipt(
        cls,
        db: Session,
        organization_id: str,
        invoice_id: str,
        unique_id: str = None,
        template_id: str = None,
        context: dict = None,
        transaction_reference: str = None,
        send_notification: bool = True,
        check_invoice_paid: bool = True,
        recipients: Optional[List[EmailStr]] = None
    ):
        '''This generates invoice receipt'''
        
        invoice = Invoice.fetch_by_id(db, invoice_id)
        
        if check_invoice_paid and invoice.status != 'paid':
            raise HTTPException(400, 'Cannot generate receipt for unpaid or unresolved invoice')
        
        # if invoice.status == "paid" and invoice.receipt is not None:
        #     raise HTTPException('Invoice has been paid for and receipt has been generated') 
        
        # Check if receipt already exists for invoice
        existing_receipt = Receipt.fetch_one_by_field(
            db=db, throw_error=False,
            organization_id=organization_id,
            invoice_id=invoice_id,
        )
        
        if existing_receipt:
            # db.delete(existing_receipt)
            # db.commit()
            raise HTTPException(400, "Receipt already exists for this invoice")
        
        receipt = Receipt.create(
            db=db,
            unique_id=(
                helpers.generate_unique_id(
                    db=db, 
                    organization_id=organization_id
                ) if not unique_id else unique_id
            ),
            invoice_id=invoice_id,
            organization_id=invoice.organization_id,
            customer_id=invoice.customer_id,
            vendor_id=invoice.vendor_id,
            order_id=invoice.order_id,
            amount=invoice.total,
            payment_date=datetime.now(),
            payment_method=invoice.payments[-1].method if invoice.payments else 'unknown',
            transaction_reference=transaction_reference
        )
        
        # Send receipt to customer
        if send_notification:
            if receipt.customer_id or receipt.vendor_id:
                if receipt.customer_id:
                    customer = Customer.fetch_by_id(db, receipt.customer_id)
                    business_partner = customer.business_partner
                    email_to_notify = business_partner.email
                    
                    template_name = 'customer-receipt.html'
                    base_template_data = {
                        "order": invoice.order.to_dict() if invoice.order_id else None,
                        'order_items': [
                            {
                                **item.to_dict(excludes=['product']),
                                'product': item.product.to_dict()
                            } for item in invoice.order.items
                        ] if invoice.order_id else None,
                    }
                
                if receipt.vendor_id:
                    vendor = Vendor.fetch_by_id(db, receipt.vendor_id)
                    business_partner = vendor.business_partner
                    email_to_notify = business_partner.email
                    
                    # Get sale data for the vendor for the month in the invoice
                    sale_data = SaleService.extract_monthly_sale_data_for_vendor(
                        db=db, organization_id=organization_id,
                        vendor_id=vendor.id,
                        month=invoice.invoice_month,
                        year=invoice.invoice_year,
                    )
                    
                    template_name = 'vendor-receipt.html'
                    base_template_data = {
                        'sale_data': sale_data
                    }
                    
                template_data = {
                    "business_partner": business_partner.to_dict(),
                    "invoice": invoice.to_dict(),
                    "receipt": receipt.to_dict(),
                    **base_template_data
                }
                
                html = None
                if template_id:
                    template_data = template_data if not context else context
                    
                    html, _, _, _ = TemplateService.render_template(
                        db=db,
                        template_id=template_id,
                        context=template_data
                    )
                
                recipients = recipients if recipients else []        
                send_email_celery.delay(
                    recipients=list(set([email_to_notify] + recipients)),
                    subject=f'Receipt for Invoice #{invoice.unique_id}',
                    template_name=template_name if not template_id else None,
                    html_template_string=html if template_id else None,
                    template_data=template_data,
                    add_pdf_attachment=True
                )
                
        return receipt
