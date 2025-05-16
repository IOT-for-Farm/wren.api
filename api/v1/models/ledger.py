from enum import Enum
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property

from api.core.base.base_model import BaseTableModel


class LedgerAccountType(str, Enum):
    asset = "asset"
    revenue = "revenue"
    contra_revenue = "contra_revenue"
    expense = "expense"
    liability = "liability"
    
    
class LedgerAccount(BaseTableModel):
    __tablename__ = "ledger_accounts"
    
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), nullable=False)
    
    name = sa.Column(sa.String, nullable=False)
    type = sa.Column(sa.String, nullable=False, default='asset')
    

class LedgerEntry(BaseTableModel):
    __tablename__ = "ledger_entries"

    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), nullable=False)
    
    # What triggered the entry
    transaction_type = sa.Column(sa.String, nullable=False, index=True)  # e.g., "order", "payment", "refund"
    model_id = sa.Column(sa.String, nullable=False, index=True)      # e.g., order.id, invoice.id
    model_name = sa.Column(sa.String, nullable=False, index=True)   # e.g., "orders", "invoices"

    # Double-entry fields
    debit_account_id = sa.Column(sa.String, sa.ForeignKey('ledger_accounts.id'), nullable=False)     # e.g., "Accounts Receivable"- where money is going to
    credit_account_id = sa.Column(sa.String, sa.ForeignKey('ledger_accounts.id'), nullable=False)    # e.g., "Sales Revenue" - where money is leaving

    amount = sa.Column(sa.Numeric(12, 2), nullable=False)
    currency_code = sa.Column(sa.String(10), default='NGN')

    description = sa.Column(sa.Text)
    timestamp = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), index=True)
    
    debit_account = relationship(
        'LedgerAccount', 
        foreign_keys=[debit_account_id], 
        uselist=False,
        lazy='selectin',
        backref='ledger_account_debit_acc'
    )
    
    credit_account = relationship(
        'LedgerAccount', 
        foreign_keys=[credit_account_id], 
        uselist=False,
        lazy='selectin',
        backref='ledger_account_credit_acc'
    )
