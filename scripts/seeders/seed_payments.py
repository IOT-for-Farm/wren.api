import sys
import pathlib
from datetime import datetime, timedelta
from decimal import Decimal

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.payment import Payment
from api.v1.models.organization import Organization
from api.v1.models.invoice import Invoice
from api.db.database import get_db_with_ctx_manager


def seed_payments():
    '''Seed payments for invoices'''
    
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
        
        # Get invoices
        invoices = Invoice.fetch_by_field(
            db=db,
            paginate=False,
            organization_id=greentrac_org.id
        )[1]  # Get the results, not the query
        
        if not invoices:
            print("No invoices found. Please run seed_invoices.py first.")
            return
        
        payments = []
        
        # Create payments for some invoices
        for invoice in invoices[:3]:  # Create payments for first 3 invoices
            # Check if payment already exists for this invoice
            existing_payment = Payment.fetch_one_by_field(
                db=db,
                throw_error=False,
                invoice_id=invoice.id,
                organization_id=greentrac_org.id
            )
            
            if not existing_payment:
                # Determine payment amount and status
                if invoice.vendor_id:  # Vendor invoice - partial payment
                    payment_amount = float(invoice.total * 0.5)  # Pay 50% of vendor invoice
                    payment_status = "successful"
                    payment_method = "bank_transfer"
                    narration = f"Partial payment for vendor invoice {invoice.id[:8]}"
                else:  # Customer invoice - full payment
                    payment_amount = float(invoice.total)
                    payment_status = "successful"
                    payment_method = "card"
                    narration = f"Payment for invoice {invoice.id[:8]}"
                
                payment_data = {
                    "organization_id": greentrac_org.id,
                    "invoice_id": invoice.id,
                    "amount": payment_amount,
                    "payment_date": datetime.now() - timedelta(days=2),
                    "method": payment_method,
                    "narration": narration,
                    "currency_code": "NGN",
                    "status": payment_status
                }
                
                new_payment = Payment.create(
                    db=db,
                    **payment_data
                )
                payments.append(new_payment)
                print(f"Payment created for invoice {invoice.id[:8]}: NGN {payment_amount} ({payment_status})")
            else:
                print(f"Payment already exists for invoice {invoice.id[:8]}")
        
        # Create some pending payments
        for invoice in invoices[3:5]:  # Create pending payments for invoices 4-5
            existing_payment = Payment.fetch_one_by_field(
                db=db,
                throw_error=False,
                invoice_id=invoice.id,
                organization_id=greentrac_org.id
            )
            
            if not existing_payment:
                payment_data = {
                    "organization_id": greentrac_org.id,
                    "invoice_id": invoice.id,
                    "amount": float(invoice.total),
                    "payment_date": datetime.now(),
                    "method": "bank_transfer",
                    "narration": f"Pending payment for invoice {invoice.id[:8]}",
                    "currency_code": "NGN",
                    "status": "pending"
                }
                
                new_payment = Payment.create(
                    db=db,
                    **payment_data
                )
                payments.append(new_payment)
                print(f"Pending payment created for invoice {invoice.id[:8]}: NGN {float(invoice.total)}")
            else:
                print(f"Payment already exists for invoice {invoice.id[:8]}")
        
        print(f"Total payments created: {len(payments)}")


if __name__ == "__main__":
    seed_payments()
