import sys
import pathlib
from datetime import datetime, timedelta

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.receipt import Receipt
from api.v1.models.organization import Organization
from api.v1.models.invoice import Invoice
from api.v1.models.order import Order
from api.db.database import get_db_with_ctx_manager


def seed_receipts():
    '''Seed receipts for paid invoices'''
    
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
        
        # Get invoices that have payments (paid invoices)
    invoices = Invoice.fetch_by_field(
        db=db,
        paginate=False,
        organization_id=greentrac_org.id,
        status="paid"  # Only get paid invoices
    )[1]  # Get the results, not the query
    
    # If no paid invoices, get invoices with payments
    if not invoices:
        all_invoices = Invoice.fetch_by_field(
            db=db,
            paginate=False,
            organization_id=greentrac_org.id
        )[1]
        
        # Filter invoices that have payments
        invoices = []
        for invoice in all_invoices:
            if invoice.payments and len(invoice.payments) > 0:
                invoices.append(invoice)
    
    if not invoices:
        print("No paid invoices found. Please run seed_invoices.py and seed_payments.py first.")
        return
    
    receipts = []
    
    # Create receipts for paid invoices
    for invoice in invoices:
        # Check if receipt already exists for this invoice
        existing_receipt = Receipt.fetch_one_by_field(
            db=db,
            throw_error=False,
            invoice_id=invoice.id,
            organization_id=greentrac_org.id
        )
        
        if not existing_receipt:
            # Get the latest payment for this invoice
            latest_payment = None
            if invoice.payments:
                latest_payment = max(invoice.payments, key=lambda p: p.payment_date)
            
            receipt_data = {
                "invoice_id": invoice.id,
                "organization_id": greentrac_org.id,
                "customer_id": invoice.customer_id,
                "vendor_id": invoice.vendor_id,
                "order_id": invoice.order_id,
                "amount": float(invoice.total),
                "payment_date": latest_payment.payment_date if latest_payment else datetime.now(),
                "payment_method": latest_payment.method if latest_payment else "bank_transfer",
                "transaction_reference": f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{invoice.id[:4]}"
            }
            
            new_receipt = Receipt.create(
                db=db,
                **receipt_data
            )
            receipts.append(new_receipt)
            print(f"Receipt created for invoice {invoice.id[:8]}: NGN {receipt_data['amount']} - Ref: {receipt_data['transaction_reference']}")
        else:
            print(f"Receipt already exists for invoice {invoice.id[:8]}")
    
    print(f"Total receipts created: {len(receipts)}")


if __name__ == "__main__":
    seed_receipts()
