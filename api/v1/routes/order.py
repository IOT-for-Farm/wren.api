from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.business_partner import BusinessPartner
from api.v1.models.customer import Customer
from api.v1.models.invoice import Invoice
from api.v1.models.product import Product
from api.v1.models.sale import Sale
from api.v1.models.user import User
from api.v1.models.order import Order, OrderItem
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.inventory import InventoryService
from api.v1.services.order import OrderService
from api.v1.schemas import order as order_schemas
from api.utils.loggers import create_logger
from api.v1.services.product import ProductService


order_router = APIRouter(prefix='/orders', tags=['Order'])
logger = create_logger(__name__)

@order_router.post("", status_code=201, response_model=success_response)
async def create_order(
    bg_tasks: BackgroundTasks,
    payload: order_schemas.OrderCreate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new order"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='order:create',
        organization_id=payload.organization_id
    )
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )
        
    if payload.additional_info:
        payload.additional_info = helpers.format_additional_info_create(payload.additional_info)
        
    
    if not payload.customer_id:
        if not (payload.customer_email or payload.customer_name):
            raise HTTPException(400, 'Provide customer name and email fields when customer id is not provided')
        
        # Check if business partner of type customer exists
        existing_business_partner = BusinessPartner.fetch_one_by_field(
            db=db, throw_error=False,
            organization_id=payload.organization_id,
            email=payload.customer_email,
            partner_type='customer'
        )
        
        if existing_business_partner:
            payload.customer_id = existing_business_partner.id
            
        else:
            # Create a new customer
            names = payload.customer_name.split(' ')
            first_name= names[0],
            last_name=names[1] if len(names) > 1 else "" ,
            
            new_business_partner = BusinessPartner.create(
                db=db,
                organization_id=payload.organization_id,
                partner_type='customer',
                email=payload.customer_email,
                first_name= first_name,
                last_name= last_name,
                phone=payload.customer_phone if payload.customer_phone else None,
                phone_country_code=payload.customer_phone_country_code if payload.customer_phone_country_code else None,
                image_url=helpers.generate_logo_url(f'{first_name} {last_name}')
            )
            
            # Create new customer as well
            Customer.create(
                db=db,
                business_partner_id=new_business_partner.id
            )
            
            payload.customer_id = new_business_partner.id
        
    order = Order.create(
        db=db,
        **payload.model_dump(exclude_unset=True, exclude=['order_items'])
    )
    
    # Create order items
    for item in payload.order_items:
        ProductService.product_belongs_to_organization(
            db=db,
            product_id=item.product_id,
            organization_id=payload.organization_id
        )
        
        try:
            # Check inventory to ensure that there is enough stock
            InventoryService.check_and_update_inventory(
                db=db,
                quantity_to_update=item.quantity,
                product_id=item.product_id
            )
        except HTTPException as e:
            order.status = "failed"
            db.commit()
            raise e
        
        OrderItem.create(
            db=db,
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )

    # TODO: Create ledger entry here
    
    logger.info(f'Order with id {order.id} created')
    
    return success_response(
        message=f"Order created successfully",
        status_code=201,
        data=order.to_dict()
    )


@order_router.get("", status_code=200)
async def get_orders(
    organization_id: str,
    unique_id: str = None,
    customer_name: str = None,
    customer_email: str = None,
    customer_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all orders"""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    query, orders, count = Order.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'customer_name': customer_name,
            'customer_email': customer_email,
            'unique_id': unique_id,
        },
        organization_id=organization_id,
        customer_id=customer_id
    )
    
    return paginator.build_paginated_response(
        items=[order.to_dict() for order in orders],
        endpoint='/orders',
        page=page,
        size=per_page,
        total=count,
    )


@order_router.get("/{id}", status_code=200, response_model=success_response)
async def get_order_by_id(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a order by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        db=db, entity=entity,
        organization_id=organization_id
    )

    order = Order.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched order successfully",
        status_code=200,
        data=order.to_dict()
    )


@order_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_order(
    id: str,
    organization_id: str,
    bg_tasks: BackgroundTasks,
    payload: order_schemas.UpdateOrder,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a order"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='order:update',
        organization_id=organization_id
    )
    
    order = Order.fetch_by_id(db, id)
    
    if order.status in ['cancelled', 'accepted', 'failed']:
        raise HTTPException(400, "You have no access to this order has it has been closed")

    order = Order.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['order_items', 'additional_info', 'additional_info_keys_to_remove'])
    )
    
    if payload.additional_info:
        order.additional_info = helpers.format_additional_info_update(
            additional_info=payload.additional_info,
            model_instance=order,
            keys_to_remove=payload.additional_info_keys_to_remove
        )
    
    db.commit()
    
    if payload.order_items:
        # Create order items
        for item in payload.order_items:
            ProductService.product_belongs_to_organization(
                db=db,
                product_id=item.product_id,
                organization_id=organization_id
            )
            
            try:
                # Check if order item exists already but the quantity is updated so you can update it
                order_item = OrderItem.fetch_one_by_field(
                    db=db, throw_error=False,
                    order_id=order.id,
                    product_id=item.product_id
                )
                
                # Delete the order item if the quantity was set to zero
                if item.quantity == 0:
                    db.delete(order_item)
                    db.commit()
                    continue
                
                if order_item and item.quantity != order_item.quantity:
                    # Get difference in quantity between user quantuty input and the quantity that exists in the database
                    # This could be negative. Once it is negative, it will increase the inventory
                    # NOTE: This should not he tampered with
                    difference_in_quantity = item.quantity - order_item.quantity
                    logger.info(f'Difference in quantity: {difference_in_quantity}')
                    
                    # Update order item
                    order_item.quantity = item.quantity
                    db.commit()
                    
                elif not order_item:
                    OrderItem.create(
                        db=db,
                        order_id=order.id,
                        product_id=item.product_id,
                        quantity=item.quantity
                    )
                    difference_in_quantity = item.quantity
                    
                else:
                    continue
                
                # Check inventory to ensure that there is enough stock
                InventoryService.check_and_update_inventory(
                    db=db,
                    quantity_to_update=difference_in_quantity,
                    product_id=item.product_id
                )
                
            except HTTPException as e:
                order.status = "failed"
                db.commit()
                raise e
            
    
    # Create invoice for order
    if payload.status == order_schemas.OrderStatus.accepted:
        # Check if there is an existing invoice for the order
        existing_invoice = Invoice.fetch_one_by_field(
            db=db, throw_error=False,
            organization_id=organization_id,
            order_id=order.id,
        )
        if existing_invoice:
            # Remove the invoice
            db.delete(existing_invoice)
            db.commit()
        
        invoice = Invoice.create(
            db=db,
            organization_id=organization_id,
            order_id=order.id,
            customer_id=order.customer_id if order.customer_id else None,
            subtotal=order.total_amount
        )
        
        order.invoice_id = invoice.id
    
        # TODO: Send notification to vendor
        
        # OrderService.send_order_notification(
        #     bg_tasks=bg_tasks,
        #     db=db,
        #     order=order,
        #     to='vendor'
        # )
        
        OrderService.send_order_notification(
            bg_tasks=bg_tasks,
            db=db,
            order=order,
            to='customer'
        )
        
        db.commit()
        
        # Create sale for the order items
        for item in order.items:
            Sale.create(
                db=db,
                product_id=item.product_id,
                organization_id=organization_id,
                quantity=item.quantity,
                customer_name=order.customer_name if order.customer_name else None,
                customer_email=order.customer_email if order.customer_email else None,
                customer_phone=order.customer_phone if order.customer_phone else None,
                customer_phone_country_code=order.customer_phone_country_code if order.customer_phone_country_code else None,
                customer_id=order.customer_id if order.customer_id else None,
                vendor_id=item.product.vendor_id if item.product.vendor_id else None
            )
            
            # TODO: Send invoice to customer and vendor if there is one

    logger.info(f'Order with id {order.id} updated')
    
    return success_response(
        message=f"Order updated successfully",
        status_code=200,
        data=order.to_dict()
    )


@order_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_order(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a order"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='order:delete',
        organization_id=organization_id
    )

    Order.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )
