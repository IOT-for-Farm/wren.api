from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from api.core.dependencies.email_sending_service import send_email
from api.utils.loggers import create_logger
from api.v1.models.customer import Customer
from api.v1.models.invoice import Invoice
from api.v1.models.order import Order
from api.v1.models.organization import Organization
from api.v1.models.vendor import Vendor
from api.v1.schemas import order as order_schemas
from api.v1.services.organization import OrganizationService


logger = create_logger(__name__)

class OrderService:
    
    @classmethod
    def send_order_notification(
        cls, 
        bg_tasks: BackgroundTasks,
        db: Session, 
        organization_id: str,
        order: Order, 
        vendor_id: str = None,  # since vendor is not part of the order. if empty, it will send to organization
        to: str = 'vendor'
    ):
        '''Function to send order notification to vendor or customer'''
        
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
            if not vendor_id:
                organization = Organization.fetch_by_id(db, organization_id)
                
                # Get order items that belong to the organization
                order_items = [
                    item for item in order.items 
                    if item.product.vendor_id is None
                    and item.product.organization_id == organization_id
                ]
                
                # Check if order items  has content before sending email to organization
                if len(order_items) == 0:
                    return
                
                # Send notification to organization members as it is an organization product
                OrganizationService.send_email_to_organization(
                    db=db,
                    bg_tasks=bg_tasks,
                    organization_id=organization_id,
                    subject='Order notification',
                    template_name='order-notification.html',
                    context={
                        'business_partner': None,
                        'organization': organization.to_dict(),
                        'order': order.to_dict(),
                        'order_items': [
                            {
                                **item.to_dict(excludes=['product']),
                                'product': item.product.to_dict()
                            } for item in order_items
                        ]
                    }
                )
                return
            
            vendor = Vendor.fetch_one_by_field(db, business_partner_id=vendor_id)
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
                'organization': None,
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
