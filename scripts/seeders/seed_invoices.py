import sys
import pathlib
from datetime import datetime, timedelta
from decimal import Decimal

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.invoice import Invoice
from api.v1.models.organization import Organization
from api.v1.models.department import Department
from api.v1.models.business_partner import BusinessPartner
from api.v1.models.customer import Customer
from api.v1.models.vendor import Vendor
from api.v1.models.order import Order
from api.db.database import get_db_with_ctx_manager


def seed_invoices():
    '''Seed invoices'''
    
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
        
        # Get customers and vendors
        customers = Customer.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        vendors = Vendor.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        # Get orders
        orders = Order.fetch_by_field(
            db=db,
            paginate=False,
            organization_id=greentrac_org.id
        )[1]  # Get the results, not the query
        
        if not customers or not orders:
            print("Required dependencies not found. Please run seed_business_partners.py and seed_orders.py first.")
            return
        
        invoices = []
        
        # Create invoices for orders
        for order in orders:
            # Check if invoice already exists for this order
            existing_invoice = Invoice.fetch_one_by_field(
                db=db,
                throw_error=False,
                order_id=order.id,
                organization_id=greentrac_org.id
            )
            
            if not existing_invoice:
                # Create invoice for the order
                invoice_data = {
                    "organization_id": greentrac_org.id,
                    "department_id": None,  # No specific department
                    "customer_id": order.customer_id,
                    "vendor_id": None,  # This is a customer invoice
                    "order_id": order.id,
                    "issue_date": datetime.now() - timedelta(days=5),
                    "due_date": datetime.now() + timedelta(days=30),
                    "status": "pending",
                    "description": f"Invoice for Order #{order.id[:8]} - {order.customer_name}",
                    "invoice_month": datetime.now().month,
                    "invoice_year": datetime.now().year,
                    "subtotal": float(order.total_amount),
                    "tax": float(order.total_amount * 0.075),  # 7.5% tax
                    "discount": 0.00,
                    "currency_code": "NGN",
                    "items": [
                        {
                            "description": f"Order #{order.id[:8]}",
                            "quantity": 1,
                            "rate": float(order.total_amount),
                            "amount": float(order.total_amount)
                        }
                    ]
                }
                
                new_invoice = Invoice.create(
                    db=db,
                    **invoice_data
                )
                invoices.append(new_invoice)
                print(f"Invoice created for Order {order.id[:8]}: NGN {new_invoice.total}")
            else:
                print(f"Invoice already exists for Order {order.id[:8]}")
        
        # Create some vendor invoices (bills we need to pay)
        for vendor in vendors[:2]:  # Create invoices for first 2 vendors
            existing_vendor_invoice = Invoice.fetch_one_by_field(
                db=db,
                throw_error=False,
                vendor_id=vendor.business_partner_id,
                organization_id=greentrac_org.id
            )
            
            if not existing_vendor_invoice:
                vendor_invoice_data = {
                    "organization_id": greentrac_org.id,
                    "department_id": None,
                    "customer_id": None,  # This is a vendor invoice
                    "vendor_id": vendor.business_partner_id,
                    "order_id": None,
                    "issue_date": datetime.now() - timedelta(days=10),
                    "due_date": datetime.now() + timedelta(days=20),
                    "status": "pending",
                    "description": f"Vendor Invoice from {vendor.business_partner.company_name or f'{vendor.business_partner.first_name} {vendor.business_partner.last_name}'}",
                    "invoice_month": datetime.now().month,
                    "invoice_year": datetime.now().year,
                    "subtotal": float(250000.00),  # Sample amount
                    "tax": float(18750.00),  # 7.5% tax
                    "discount": 0.00,
                    "currency_code": "NGN",
                    "items": [
                        {
                            "description": "Product supply and delivery",
                            "quantity": 1,
                            "rate": float(250000.00),
                            "amount": float(250000.00)
                        }
                    ]
                }
                
                new_vendor_invoice = Invoice.create(
                    db=db,
                    **vendor_invoice_data
                )
                invoices.append(new_vendor_invoice)
                print(f"Vendor invoice created for {vendor.business_partner.company_name or f'{vendor.business_partner.first_name} {vendor.business_partner.last_name}'}: NGN {new_vendor_invoice.total}")
            else:
                print(f"Vendor invoice already exists for {vendor.business_partner.company_name or f'{vendor.business_partner.first_name} {vendor.business_partner.last_name}'}")
        
        print(f"Total invoices created: {len(invoices)}")


if __name__ == "__main__":
    seed_invoices()
