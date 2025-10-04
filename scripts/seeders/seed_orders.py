import sys
import pathlib
from datetime import datetime, timedelta

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.order import Order, OrderItem
from api.v1.models.organization import Organization
from api.v1.models.customer import Customer
from api.v1.models.product import Product
from api.db.database import get_db_with_ctx_manager


def seed_orders():
    '''Seed orders and order items'''
    
    with get_db_with_ctx_manager() as db:
        # Get required dependencies
        greentrac_org = Organization.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug="greentrac-tech"
        )
        
        customers = Customer.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        products = Product.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        if not greentrac_org or not customers or not products:
            print("Required dependencies not found. Please run seed_organizations.py, seed_customers.py, and seed_products.py first.")
            return
        
        orders = []
        
        # Create orders for each customer
        for customer in customers:
            # Create 1-3 orders per customer
            num_orders = 2  # Default number of orders
            
            for order_num in range(num_orders):
                order_data = {
                    "organization_id": greentrac_org.id,
                    "invoice_id": None,  # Will be set when invoice is created
                    "customer_name": f"{customer.business_partner.first_name} {customer.business_partner.last_name}",
                    "customer_email": customer.business_partner.email,
                    "customer_phone": customer.business_partner.phone,
                    "customer_phone_country_code": customer.business_partner.phone_country_code,
                    "customer_id": customer.business_partner_id,
                    "currency_code": "NGN",
                    "status": "completed" if order_num == 0 else "pending",
                    "additional_info": {
                        "order_source": "website",
                        "shipping_address": "Same as billing address",
                        "notes": f"Order #{order_num + 1} from {customer.business_partner.company_name or 'Individual Customer'}"
                    }
                }
                
                existing_order = Order.fetch_one_by_field(
                    db=db,
                    throw_error=False,
                    customer_id=customer.business_partner_id,
                    organization_id=greentrac_org.id
                )
                
                if not existing_order or order_num > 0:
                    new_order = Order.create(
                        db=db,
                        **order_data
                    )
                    orders.append(new_order)
                    print(f"Order created for {customer.business_partner.first_name} {customer.business_partner.last_name}")
                    
                    # Create order items (1-3 items per order)
                    num_items = min(3, len(products))
                    selected_products = products[:num_items]  # Take first few products
                    
                    for i, product in enumerate(selected_products):
                        quantity = (i + 1) * 2  # 2, 4, 6 quantities
                        
                        order_item_data = {
                            "order_id": new_order.id,
                            "product_id": product.id,
                            "quantity": quantity
                        }
                        
                        new_order_item = OrderItem.create(
                            db=db,
                            **order_item_data
                        )
                        print(f"  - Order item created: {product.name} x{quantity}")
        
        print(f"Total orders created: {len(orders)}")


if __name__ == "__main__":
    seed_orders()
