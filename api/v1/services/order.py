from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from api.core.dependencies.email_sending_service import send_email
from api.utils.loggers import create_logger
from api.v1.models.customer import Customer
from api.v1.models.invoice import Invoice
from api.v1.models.order import Order
from api.v1.models.vendor import Vendor
from api.v1.schemas import order as order_schemas


logger = create_logger(__name__)

class OrderService:
    
    @classmethod
    def send_order_notification(
        cls, 
        bg_tasks: BackgroundTasks,
        db: Session, 
        order: Order, 
        to: str = 'vendor'
    ):
        '''Function to send order notification to vendor or customer'''
        
        # Get invoice from order
        invoice = Invoice.fetch_by_id(db, order.invoice_id)
        
        if to == 'customer':
            if order.customer_id:
                customer = Customer.fetch_one_by_field(db, business_partner_id=order.customer_id)
                business_partner = customer.business_partner.to_dict()
                email_to_notify = business_partner['email']
            else:
                names = order.customer_name.split(' ')
                business_partner = {
                    'email': order.customer_email,
                    'first_name': names[0],
                    'last_name': names[1] if len(names) > 1 else "" ,
                    'phone': order.customer_phone,
                    'phone_country_code': order.customer_phone_country_code,
                    'partner_type': 'customer'
                }
                email_to_notify = business_partner['email']
                            
            # Get order items to include in the email
            order_items = order.items
        
        elif to == 'vendor':
            if not invoice.vendor_id:
                raise HTTPException(400, "This invoice is not attached to a vendor")
            
            vendor = Vendor.fetch_one_by_field(db, business_partner_id=invoice.vendor_id)
            business_partner = vendor.business_partner.to_dict()
            email_to_notify = business_partner['email']
            
            # Get order items to include in the email
            order_items = [item for item in order.items if item.product.vendor_id==vendor.business_partner_id]
        
        else:
            raise HTTPException(400, f'Expecting vendor or customer. Got `{to}`') 
        
        # TODO: Send email notification or register email for sending
        bg_tasks.add_task(
            send_email,
            recipients=[email_to_notify],
            template_name='order-notification.html',
            subject='Order notification',
            template_data={
                'business_partner': business_partner,
                'order': order.to_dict(),
                'order_items': [
                    {
                        **item.to_dict(excludes=['product']),
                        'product': item.product.to_dict()
                    } for item in order_items
                ]
            }
        )
