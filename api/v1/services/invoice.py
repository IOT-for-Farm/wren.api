from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import EmailStr
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from fastapi import HTTPException

from api.utils import helpers
from api.utils.loggers import create_logger
from api.v1.models.customer import Customer
from api.v1.models.invoice import Invoice
from api.v1.models.order import Order
from api.v1.models.sale import Sale
from api.v1.models.vendor import Vendor
from api.v1.schemas import invoice as invoice_schemas
from api.v1.schemas.order import OrderStatus
from api.v1.services.sale import SaleService
from api.v1.services.template import TemplateService


logger = create_logger(__name__)

class InvoiceService:
    
    @classmethod
    def generate_custom_invoice(
        cls,
        db: Session, 
        organization_id: str,
        unique_id: str,
        due_date: datetime = None,
        currency_code: str = 'NGN',
        template_id: str = None,
        description: str = None,
        customer_id: str = None,
        context: dict = None,
        send_notification: bool = False,
        recipients: Optional[List[EmailStr]] = None,
        items: Optional[List[invoice_schemas.InvoiceItem]] = None
    ):
        from api.core.dependencies.celery.queues.email.tasks import send_email_celery
        
        invoice_items = []
        if items:
            for item in items:
                invoice_items.append({
                    "rate": item.rate,
                    "quantity": item.quantity,
                    "description": item.description,
                })
        
        customer = None
        if customer_id:
            customer = Customer.fetch_one_by_field(db, business_partner_id=customer_id)
        
        invoice = Invoice.create(
            db=db,
            unique_id=unique_id,
            organization_id=organization_id,
            due_date=due_date,
            currency_code=currency_code,
            description=description,
            invoice_month=datetime.now().month,
            invoice_year=datetime.now().year,
            items=invoice_items,
            customer_id=customer_id
        )
        
        if send_notification:
            template_data=invoice.to_dict()
            
            if customer:
                template_data['customer'] = customer.to_dict()
            
            # TODO: Send invoice notification to user
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
                recipients=recipients + [customer.business_partner.email],
                subject=f'Here is your invoice',
                template_name='invoice-detail.html' if not template_id else None,
                html_template_string=html if template_id else None,
                template_data=template_data,
                add_pdf_attachment=True
            )
        
        return invoice
                
    
    @classmethod
    def generate_order_invoice(
        cls,
        db: Session, 
        organization_id: str,
        unique_id: str,
        order_id: str,
        due_date: datetime = None,
        currency_code: str = 'NGN',
        template_id: str = None,
        context: dict = None,
        send_notification: bool = False,
        recipients: Optional[List[EmailStr]] = None
    ):
        '''Fucntion to generate invoice for an order'''
        
        from api.core.dependencies.celery.queues.email.tasks import send_email_celery
        
        order = Order.fetch_by_id(db, order_id)
        
        if order.status != OrderStatus.accepted.value:
            raise HTTPException(400, 'Can only generate invoice for accepted orders')
                
        existing_invoice = Invoice.fetch_one_by_field(
            db=db, throw_error=False,
            organization_id=organization_id,
            order_id=order.id,
        )
        
        if existing_invoice:
            # Remove the invoice
            # existing_invoice.is_deleted = True
            db.delete(existing_invoice)
            db.commit()
        
        invoice = Invoice.create(
            db=db,
            unique_id=unique_id,
            organization_id=organization_id,
            order_id=order.id,
            customer_id=order.customer_id if order.customer_id else None,
            subtotal=order.total_amount,
            due_date=due_date,
            currency_code=currency_code,
            description=f"""Invoice for order {order.unique_id} for {order.customer.first_name} {order.customer.last_name}.
Number of items in order: {len(order.items)}
            """,
            invoice_month=datetime.now().month,
            invoice_year=datetime.now().year,
        )
        
        # Update order to include attach the invouce id
        order.invoice_id = invoice.id
        db.commit()
        
        if send_notification:
            template_data={
                'business_partner': order.customer.business_partner.to_dict(),
                'order': order.to_dict(),
                'order_items': [
                    {
                        **item.to_dict(excludes=['product']),
                        'product': item.product.to_dict()
                    } for item in order.items
                ]
            }
            
            # TODO: Send invoice notification to user
            html = None
            if template_id:
                template_data = template_data if not context else context
                
                html, _, _, _ = TemplateService.render_template(
                    db=db,
                    template_id=template_id,
                    context=template_data
                )
            
            recipients = recipients if recipients else []
            
            # This will remove duplicate emails in case of a case where customer email is sent twice
            recipients_to_send_to = list(set([order.customer.business_partner.email] + recipients))
            
            send_email_celery.delay(
                recipients=recipients_to_send_to,
                subject=f'Invoice for your order #{order.unique_id}',
                template_name='order-notification.html' if not template_id else None,
                html_template_string=html if template_id else None,
                template_data=template_data,
                add_pdf_attachment=True
            )
        
        return invoice
    
    
    @classmethod
    def generate_vendor_invoice(
        cls,
        db: Session,
        organization_id: str,
        unique_id: str,
        vendor_id: str,
        due_date: datetime = None,
        year_to_generate_for: int = None,
        month_to_generate_for: int = None,
        currency_code: str = 'NGN',
        template_id: str = None,
        context: dict = None,
        send_notification: bool = True,
        recipients: Optional[List[EmailStr]] = None
    ):
        '''Fucntion to generate an invice for a vendor based on sales over a 30 day period'''
        
        from api.core.dependencies.celery.queues.email.tasks import send_email_celery
        
        vendor = Vendor.fetch_one_by_field(
            db=db,
            business_partner_id=vendor_id
        )
        
        year = datetime.now().year if not year_to_generate_for else year_to_generate_for
        month = datetime.now().month if not month_to_generate_for else month_to_generate_for
        
        # Full month name
        month_str = datetime(year, month, 1).strftime('%B')  # "January" to "December"
        
        start_date = datetime(year, month, 1)
        end_date =start_date + timedelta(days=30)
        
        # Fetch vendor sales
        query = db.query(Sale).filter(
            Sale.organization_id == organization_id,
            Sale.vendor_id == vendor.id,
            Sale.is_deleted == False,
        ).filter(
            and_(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date    
            )
        )
        
        sale_count = query.count()
        sales = query.all()
        
        if sale_count == 0:
            raise HTTPException(400, 'No sales made by the vendor in the specified time perios')
        
        amount_owed = sum([sale.organization_profit for sale in sales])
        total_items_sold = sum([sale.quantity for sale in sales])
        
        # Check if invoice already exists for the month and year for the vendor
        existing_invoice = Invoice.fetch_one_by_field(
            db=db, throw_error=False,
            vendor_id=vendor.id,
            organization_id=organization_id,
            invoice_month=month,
            invoice_year=year
        )
        
        if existing_invoice:
            # raise HTTPException(400, f'Invoice already exists for {month_str} {year} for this vendor')
            db.delete(existing_invoice)
            db.commit()
        
        invoice = Invoice.create(
            db=db,
            unique_id=unique_id,
            organization_id=organization_id,
            vendor_id=vendor.id,
            subtotal=amount_owed,
            due_date=due_date,
            currency_code=currency_code,
            description=f"""Invoice for {month_str} {year} for {vendor.business_partner.company_name}.
Number of sales: {sale_count}.
Total number of items sold: {total_items_sold}.
Commission agreement: {vendor.commission_percentage}%""",
            invoice_month=month,
            invoice_year=year,
        )
        
        if send_notification:
            sale_data = SaleService.extract_monthly_sale_data_for_vendor(
                db=db, organization_id=organization_id,
                vendor_id=vendor.id,
                month=invoice.invoice_month,
                year=invoice.invoice_year,
            )
            
            template_data = {
                'business_partner': vendor.business_partner.to_dict(),
                "sale_data": sale_data
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
            
            # This will remove duplicate emails in case of a case where vendor email is sent twice
            recipients_to_send_to = list(set([vendor.business_partner.email] + recipients))
            
            send_email_celery.delay(
                recipients=recipients_to_send_to,
                subject=f'Invoice for the month of {month_str} {year}',
                template_name='vendor-invoice.html' if not template_id else None,
                html_template_string=html if template_id else None,
                template_data=template_data,
                add_pdf_attachment=True
            )
        
        return invoice
