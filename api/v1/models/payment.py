import sqlalchemy as sa
from sqlalchemy import event
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel
from api.db.database import SessionLocal, get_db_with_ctx_manager
from api.v1.models.invoice import Invoice


class Payment(BaseTableModel):
    __tablename__ = 'payments'

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    invoice_id = sa.Column(sa.String, sa.ForeignKey("invoices.id"), index=True)
    amount = sa.Column(sa.Numeric(12, 2), nullable=False)
    payment_date = sa.Column(sa.DateTime, default=sa.func.now())
    method = sa.Column(sa.String, default='cash', index=True)  # e.g. "bank_transfer", "card", "cash"
    narration = sa.Column(sa.String, nullable=True)
    currency_code = sa.Column(sa.String(10), default='NGN')
    status = sa.Column(sa.String, default="pending", index=True)

    refunds = relationship('Refund', back_populates='payment', lazy='selectin')
    invoice = relationship("Invoice", back_populates="payments")
    
    

def update_invoice_status(mapper, connection, target):
    """
    Automatically updates the associated invoice's status when:
    - A new payment is added
    - An existing payment is modified
    """
    
    with get_db_with_ctx_manager() as db:
        try:
            invoice = Invoice.fetch_by_id(db, target.invoice_id)
            
            # Calculate total paid (using existing relationship)
            total_paid = sum(p.amount for p in invoice.payments if p.status != "failed")
            
            # # Update invoice status based on payment conditions
            if total_paid >= float(invoice.total):
                invoice.status = 'paid'
            else:
                invoice.status = 'pending'  # Or 'partial' if you want to track partial payments
            
            db.commit()
            
            # invoice.update_invoice_payment_status(db)
        
        except Exception as e:
            db.rollback()
            raise e
        
        finally:
            db.close()


event.listen(Payment, 'after_insert', update_invoice_status)
event.listen(Payment, 'after_update', update_invoice_status)
