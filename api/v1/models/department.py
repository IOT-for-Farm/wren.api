import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session, backref

from api.core.base.base_model import BaseTableModel


class Department(BaseTableModel):
    __tablename__ = "departments"
    
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    creator_id = sa.Column(sa.String, sa.ForeignKey("users.id"), index=True)
    name = sa.Column(sa.String(100), nullable=False)
    parent_id = sa.Column(sa.String, sa.ForeignKey("departments.id", ondelete="cascade"), index=True)
    additional_info = sa.Column(sa.JSON, default={})
    is_active = sa.Column(sa.Boolean, server_default='true')
    
    # Relationships
    organization = relationship("Organization", backref="org_departments")
    created_by = relationship("User", backref="user_departments", lazy='selectin')
    # parent = relationship(
    #     "Department", 
    #     remote_side='Department.id', 
    #     uselist=False, 
    #     foreign_keys=[parent_id],
    #     lazy='selectin'
    # )
    
    parent = relationship(
        "Department", 
        remote_side='Department.id', 
        uselist=False, 
        foreign_keys=[parent_id],
        lazy='selectin',
        backref=backref('sub_departments',  cascade="all, delete-orphan"), 
        post_update=True, 
        single_parent=True, 
    )
    
    # children = relationship(
    #     "Department", 
    #     overlaps='parent', 
    #     lazy='selectin'
    # )
    
    roles = relationship(
        "DepartmentRole", 
        backref="department",
        primaryjoin="and_(Department.id == foreign(DepartmentRole.department_id), DepartmentRole.is_deleted == False)",  # add Department.id=='-1' for default roles to show
        # primaryjoin="and_(Department.id == foreign(DepartmentRole.department_id), Department.id == -1, DepartmentRole.is_deleted == False)",  # add Department.id=='-1' for default roles to show
        lazy="selectin"
    )
    # members = relationship(
    #     "User",
    #     # primaryjoin="and_(User.id == DepartmentMember.user_id, DepartmentMember.is_deleted == False)",   
    #     secondary='user_departments',
    #     backref="departments",
    #     lazy='selectin'
    # )
    

class DepartmentBudget(BaseTableModel):
    __tablename__ = "department_budgets"
    
    department_id = sa.Column(sa.String, sa.ForeignKey("departments.id"), nullable=False, index=True)
    fiscal_year = sa.Column(sa.Integer, nullable=False, index=True)  # 2024, 2025
    period_type = sa.Column(sa.String, default="annual")  # annual/quarterly/monthly
    
    # Amounts
    allocated_amount = sa.Column(sa.Numeric(12, 2), nullable=False)  # Planned budget
    utilized_amount = sa.Column(sa.Numeric(12, 2), default=0.00)     # Actual spend
    pending_amount = sa.Column(sa.Numeric(12, 2), default=0.00)      # Approved but not spent
    
    # Tracking
    currency = sa.Column(sa.String(3), default="NGN")  # ISO currency code
    fiscal_period_start = sa.Column(sa.Date)  # 2024-01-01 for annual
    fiscal_period_end = sa.Column(sa.Date)    # 2024-12-31
    
    # Relationships
    department = relationship("Department", backref='department_budgets')
    adjustments = relationship("BudgetAdjustment", backref="department_budgets", lazy='selectin')
    
    __table_args__ = (
        sa.UniqueConstraint("department_id", "fiscal_year", "period_type", name="uq_budget_period"),
    )


class BudgetAdjustment(BaseTableModel):
    __tablename__ = "budget_adjustments"
    
    budget_id = sa.Column(sa.String, sa.ForeignKey("department_budgets.id"), index=True)
    amount = sa.Column(sa.Numeric(12, 2))  # Positive for increases, negative for decreases
    reason = sa.Column(sa.String)
    notes = sa.Column(sa.Text)
    status = sa.Column(sa.String, default="pending")  # pending/approved/rejected
    requester_id = sa.Column(sa.String, sa.ForeignKey("users.id"), index=True)
    approver_id = sa.Column(sa.String, sa.ForeignKey("users.id"), nullable=True, index=True)
    
    # Relationships
    requester = relationship(
        "User", 
        foreign_keys=[requester_id], 
        backref="budget_requests", 
        lazy='selectin', 
        uselist=False
    )
    approver = relationship(
        "User", 
        foreign_keys=[approver_id], 
        backref="budget_approvals", 
        lazy='selectin', 
        uselist=False
    )
    # budget = relationship("DepartmentBudget", back_populates="adjustments", lazy='selectin')

    

class DepartmentRole(BaseTableModel):
    __tablename__ = "department_roles"
    
    department_id = sa.Column(sa.String)
    role_name = sa.Column(sa.String)  # "Manager", "Reviewer", etc.
    description = sa.Column(sa.String)
    permissions = sa.Column(sa.JSON, default=[])  # []


class DepartmentMember(BaseTableModel):
    __tablename__ = "department_members"
    
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id"))
    department_id = sa.Column(sa.String, sa.ForeignKey("departments.id"))
    role_id = sa.Column(sa.String, sa.ForeignKey("department_roles.id"))
    is_primary = sa.Column(sa.Boolean, server_default='false')
    join_date = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    
    role = relationship(
        'DepartmentRole', 
        backref='department_members', 
        uselist=False, 
        lazy='selectin'
    )
    
    user = relationship(
        'User',
        backref="departments",
        uselist=False,
        lazy='selectin'
    )
    
    department = relationship(
        'Department',
        backref='department_members'
    )
