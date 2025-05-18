from sqlalchemy import event
import datetime as dt
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property

from api.core.base.base_model import BaseTableModel
from api.utils import helpers
from api.v1.models.customer import Customer
from api.v1.models.receipt import Receipt  # Assuming you have a Receipt model
from api.db.database import SessionLocal
from api.v1.schemas.payment import PaymentStatus


class Invoice(BaseTableModel):
    __tablename__ = 'invoices'

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    department_id = sa.Column(sa.String, sa.ForeignKey("departments.id"), index=True)
    customer_id = sa.Column(sa.String, sa.ForeignKey("business_partners.id"), index=True)
    vendor_id = sa.Column(sa.String, sa.ForeignKey("business_partners.id"), index=True)
    order_id = sa.Column(sa.String, sa.ForeignKey("orders.id"), nullable=True, index=True)
    
    issue_date = sa.Column(sa.DateTime, default=sa.func.now())
    due_date = sa.Column(sa.DateTime)
    status = sa.Column(sa.String, default="pending", index=True)
    
    description = sa.Column(sa.Text)
    invoice_month = sa.Column(sa.Integer)
    invoice_year = sa.Column(sa.Integer)
    
    subtotal = sa.Column(sa.Numeric(12, 2))
    tax = sa.Column(sa.Numeric(12, 2), default=0.00)
    discount = sa.Column(sa.Numeric(12, 2), default=0.00)
    
    currency_code = sa.Column(sa.String(10), default='NGN')
    # total = sa.Column(sa.Numeric(12, 2))

    payments = relationship("Payment", back_populates="invoice", lazy="selectin")
    organization = relationship("Organization", backref="invoices", uselist=False, lazy="selectin")
    department = relationship("Department", backref="invoices", uselist=False, lazy="selectin")
    order = relationship('Order', backref='order_invoice', foreign_keys=[order_id], uselist=False)
    receipt = relationship("Receipt", backref="invoice", lazy="selectin", uselist=False)
    
    @hybrid_property
    def total(self):
        '''Get total amount for invoice'''
        
        return (self.subtotal or 0) + (self.tax or 0) - (self.discount or 0)
    
    @hybrid_property
    def amount_paid(self):
        '''Get total amount paid'''
        
        total_paid = 0.00
        total_refunded = 0.00
        
        for payment in self.payments:
            if payment.status != PaymentStatus.successful.value:
                continue
            
            total_paid += float(payment.amount)
            
            # Get total refunds
            refunded_amount = sum([refund.amount for refund in payment.refunds if refund.status=="successful"])
            total_refunded += float(refunded_amount)
            
        return total_paid - total_refunded
    
    @hybrid_property
    def amount_remaining(self):
        '''Get total amount remaining to be paid in the invoice'''
        
        total_paid = self.amount_paid
        total_remaining = float(self.total) - total_paid
        
        return total_remaining

    @hybrid_property
    def payment_complete(self):
        '''Check though all payments to know if payment is complete'''
        
        total_paid = self.amount_paid
        return total_paid >= float(self.total)
    
    @hybrid_property
    def is_overdue(self):
        '''Check if invoice is over due'''
        
        if self.due_date:
            return self.due_date <= dt.datetime.now()
        
        return False
    
    def update_invoice_payment_status(self, db: Session):
        """Call this explicitly after payments change"""
        
        if self.amount_paid >= float(self.total):
            self.status = 'paid'
            
        elif self.due_date and (self.due_date <= dt.datetime.now()):
            self.status = 'overdue'
            
        db.commit()  # Explicit save
        

    def to_dict(self, excludes=[]):
        return {
            'total': self.total,
            'amount_paid': self.amount_paid,
            'amount_remaining': self.amount_remaining,
            'payment_complete': self.payment_complete,
            'is_overdue': self.is_overdue,
            **super().to_dict(excludes),
        }


def generate_receipt_for_paid_invoice(mapper, connection, target):
    """
    Generates a receipt when an invoice's status changes to 'paid'
    """
    
    from api.v1.services.receipt import ReceiptService
        
    
    db = SessionLocal()
    
    try:
        # Only proceed if status changed to 'paid'
        # if target.status == 'paid' and db.is_modified(target, 'status'):
        if target.status == 'paid':
            # Check if a receipt already exists for this invoice
            existing_receipt = db.query(Receipt).filter_by(invoice_id=target.id).first()
            
            if not existing_receipt:
                ReceiptService.generate_receipt(
                    db=db,
                    invoice_id=target.id,
                    organization_id=target.organization_id,
                    check_invoice_paid=False
                )
                
    except Exception as e:
        db.rollback()
        raise e
    
    finally:
        db.close()

# Register the event
event.listen(Invoice, 'after_update', generate_receipt_for_paid_invoice)
