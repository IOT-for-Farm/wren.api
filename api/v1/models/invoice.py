import datetime as dt
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property

from api.core.base.base_model import BaseTableModel


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
    
    subtotal = sa.Column(sa.Numeric(12, 2))
    tax = sa.Column(sa.Numeric(12, 2), default=0.00)
    discount = sa.Column(sa.Numeric(12, 2), default=0.00)
    # total = sa.Column(sa.Numeric(12, 2))

    payments = relationship("Payment", back_populates="invoice", lazy="selectin")
    organization = relationship("Organization", backref="invoices", uselist=False, lazy="selectin")
    department = relationship("Department", backref="invoices", uselist=False, lazy="selectin")
    order = relationship('Order', backref='order_invoice', foreign_keys=[order_id], uselist=False)
    
    @hybrid_property
    def total(self):
        '''Get total amount for invoice'''
        
        return (self.subtotal or 0) + (self.tax or 0) - (self.discount or 0)
    
    @hybrid_property
    def amount_paid(self):
        '''Get total amount paid'''
        
        total_paid = 0.00
        
        for payment in self.payments:
            total_paid += float(payment.amount)
        
        return total_paid
    
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
        
        # total_paid = 0.00
        
        # for payment in self.payments:
        #     total_paid += payment.amount
        
        if total_paid == float(self.total):
            self.status = 'paid'
            return True
        else:
            return False
    
    @hybrid_property
    def is_overdue(self):
        '''Check if invoice is over due'''
        
        if self.due_date < dt.datetime.now():
            self.status = 'overdue'
            return True
        else:
            return False

    def to_dict(self, excludes=[]):
        return {
            'total': self.total,
            'amount_paid': self.amount_paid,
            'amount_remaining': self.amount_remaining,
            'payment_complete': self.payment_complete,
            'is_overdue': self.is_overdue,
            **super().to_dict(excludes),
        }