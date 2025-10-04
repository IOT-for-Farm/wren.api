import sys
import pathlib
from datetime import datetime, timedelta

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.sale import Sale
from api.v1.models.organization import Organization
from api.v1.models.product import Product
from api.v1.models.customer import Customer
from api.v1.models.vendor import Vendor
from api.db.database import get_db_with_ctx_manager


def seed_sales():
    '''Seed sales records'''
    
    with get_db_with_ctx_manager() as db:
        # Get required dependencies
        greentrac_org = Organization.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug="greentrac-tech"
        )
        
        if not greentrac_org:
            print("Required organization not found. Please run seed_organizations.py first.")
            return
        
        # Get products
        products = Product.fetch_by_field(
            db=db,
            paginate=False,
            organization_id=greentrac_org.id
        )[1]  # Get the results, not the query
        
        # Get customers
        customers = Customer.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        # Get vendors
        vendors = Vendor.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        if not products or not customers:
            print("Required dependencies not found. Please run seed_products.py and seed_customers.py first.")
            return
        
        sales = []
        
        # Create sales for each product with different customers
        for i, product in enumerate(products):
            # Cycle through customers
            customer = customers[i % len(customers)]
            
            # Get vendor for this product (if any)
            product_vendor = None
            if product.vendor_id:
                product_vendor = Vendor.fetch_one_by_field(
                    db=db,
                    throw_error=False,
                    business_partner_id=product.vendor_id
                )
            
            # Check if sale already exists for this product-customer combination
            existing_sale = Sale.fetch_one_by_field(
                db=db,
                throw_error=False,
                product_id=product.id,
                customer_id=customer.business_partner_id,
                organization_id=greentrac_org.id
            )
            
            if not existing_sale:
                # Create sale with realistic quantity
                quantity = 2 if "400W" in product.name else (1 if "5kW" in product.name or "10kWh" in product.name else 3)
                
                sale_data = {
                    "product_id": product.id,
                    "organization_id": greentrac_org.id,
                    "quantity": quantity,
                    "customer_name": f"{customer.business_partner.first_name} {customer.business_partner.last_name}",
                    "customer_email": customer.business_partner.email,
                    "customer_phone": customer.business_partner.phone,
                    "customer_phone_country_code": customer.business_partner.phone_country_code,
                    "currency_code": "NGN",
                    "customer_id": customer.business_partner_id,
                    "vendor_id": product_vendor.business_partner_id if product_vendor else None
                }
                
                new_sale = Sale.create(
                    db=db,
                    **sale_data
                )
                sales.append(new_sale)
                
                # Calculate profit information
                total_price = new_sale.total_price_of_sale
                profit = new_sale.profit_on_sale
                org_profit = new_sale.organization_profit
                vendor_profit = new_sale.vendor_profit
                
                print(f"Sale created for {product.name} to {customer.business_partner.first_name} {customer.business_partner.last_name}")
                print(f"  - Quantity: {quantity}, Total: NGN {total_price:,.2f}")
                print(f"  - Profit: NGN {profit:,.2f} (Org: NGN {org_profit:,.2f}, Vendor: NGN {vendor_profit:,.2f})")
            else:
                print(f"Sale already exists for {product.name} to {customer.business_partner.first_name} {customer.business_partner.last_name}")
        
        # Create additional sales for popular products
        popular_products = [p for p in products if "400W" in p.name or "320W" in p.name]
        
        for product in popular_products:
            for customer in customers[:2]:  # Create additional sales for first 2 customers
                existing_sale = Sale.fetch_one_by_field(
                    db=db,
                    throw_error=False,
                    product_id=product.id,
                    customer_id=customer.business_partner_id,
                    organization_id=greentrac_org.id
                )
                
                if not existing_sale:
                    quantity = 1  # Additional single unit sales
                    
                    sale_data = {
                        "product_id": product.id,
                        "organization_id": greentrac_org.id,
                        "quantity": quantity,
                        "customer_name": f"{customer.business_partner.first_name} {customer.business_partner.last_name}",
                        "customer_email": customer.business_partner.email,
                        "customer_phone": customer.business_partner.phone,
                        "customer_phone_country_code": customer.business_partner.phone_country_code,
                        "currency_code": "NGN",
                        "customer_id": customer.business_partner_id,
                        "vendor_id": None  # Direct sales
                    }
                    
                    new_sale = Sale.create(
                        db=db,
                        **sale_data
                    )
                    sales.append(new_sale)
                    print(f"Additional sale created for {product.name} to {customer.business_partner.first_name} {customer.business_partner.last_name}")
        
        print(f"Total sales created: {len(sales)}")


if __name__ == "__main__":
    seed_sales()
