from datetime import date, timedelta
from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from api.db.database import get_db
from api.utils import helpers
from api.utils.loggers import create_logger
from api.v1.models.department import Department, DepartmentBudget, DepartmentMember, DepartmentRole
from api.v1.models.user import User
from api.v1.schemas.auth import AuthenticatedEntity, EntityType
from api.v1.schemas.department import BudgetPeriodType, DepartmentBudgetBase, DepartmentBudgetUpdate


logger = create_logger(__name__)

class DepartmentService:
    
    @classmethod
    def role_exists_in_department(cls, db: Session, department_id: str, role_id: str):
        '''Function to check if a role exists in the department'''
        
        # Check if department exists
        department = Department.fetch_by_id(db, department_id)
        
        # Check if role id exists in the department or in the default department
        role_exists = db.query(DepartmentRole).filter(
            or_(
                DepartmentRole.department_id == '-1',
                DepartmentRole.department_id == department.id,
            )
        ).filter(DepartmentRole.id == role_id, DepartmentRole.is_deleted==False).first()
        
        if not role_exists:
            raise HTTPException(400, 'Selected role does not exist in this department')
        
        return True
    
    @classmethod
    def belongs_to_department(
        cls, 
        entity: AuthenticatedEntity,
        department_id: str,
        db: Session = Depends(get_db)
    ):
        '''Function to check if an authenticated endtity belongs to an department'''
        
        
        # Check if department exists
        department = Department.fetch_by_id(db, department_id)
        
        if entity.type == EntityType.USER:
            user: User = entity.entity
        
            if user.is_superuser:
                return True
            
            # Check if user exists in department
            deprtment_member_exists = DepartmentMember.fetch_one_by_field(
                db=db, throw_error=False,
                department_id=department.id,
                user_id=user.id
            )
            
            if deprtment_member_exists:
                return True
        
        if entity.type == EntityType.APIKEY:
            raise HTTPException(403, 'API keys do not have access to departments')
        
        logger.info(f'Entity ({entity.type.value}) does not belong to this department')
        raise HTTPException(403, 'You do not have the permission to access this resource')    
        
    
    @classmethod
    def has_department_permission(
        cls, 
        entity: AuthenticatedEntity,
        department_id: str,
        permission: str,
        db: Session = Depends(get_db)
    ):
        '''Function to check if an authenticated endtity has the permission to handle an action'''
        
        # Check if entity belongs to department first
        cls.belongs_to_department(entity, department_id, db)
        
        if entity.type == EntityType.USER:
            user: User = entity.entity
        
            if user.is_superuser:
                return True  
            
            department_member = DepartmentMember.fetch_one_by_field(
                db=db, throw_error=False,
                department_id=department_id,
                user_id=user.id
            )
            
            # Extract list or permissions from org user roles
            role = department_member.role
            permissions = role.permissions
        
            if permission in permissions:
                return True
            
        if entity.type == EntityType.APIKEY:
            raise HTTPException(403, 'API keys do not have access to departments')
            
        logger.info(f'Entity ({entity.type.value}) with role `{role.role_name}` does not have `{permission}` in the list of permissions:\n{permissions}')
        raise HTTPException(403, 'You do not have the permission to access this resource')    

    
    @classmethod
    def get_user_departments(cls, db: Session, user_id: str, name: Optional[str] = None):
        '''Function to get a users departments'''
        
        query = (
            db.query(Department)
            .join(DepartmentMember, DepartmentMember.department_id == Department.id)
            .join(User, User.id == DepartmentMember.user_id)
            .filter(
                and_(
                    User.id == user_id, 
                    Department.is_deleted == False, 
                    DepartmentMember.is_deleted == False
                )
            )
        )
        
        if name:
            name_search = f"%{name}%"
            query = query.filter(Department.name.ilike(name_search))
        
        query = query.order_by(DepartmentMember.join_date.desc())
        
        departments = query.all()
        
        return departments

    
    @classmethod
    def get_department_members(
        cls, 
        db: Session, 
        department_id: str, 
        page: int,
        per_page: int,
        sort_by: str,
        order: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None
    ):
        '''Function to get department members'''
        
        query = (
            db.query(DepartmentMember)
            .join(User, DepartmentMember.user_id == User.id)
            .filter(
                DepartmentMember.department_id == department_id,
                DepartmentMember.is_deleted == False
            )
        )
        
        if full_name:
            names = full_name.split(' ')
            if len(names) > 1:
                first_name, last_name = f'%{names[0]}%', f'%{names[-1]}%'
            else:
                first_name, last_name = f'%{names[0]}%', None
            
            query = query.filter(User.first_name.ilike(first_name))
            
            if last_name:
                query = query.filter(User.last_name.ilike(last_name))
        
        if email:
            query = query.filter(User.email.ilike(f'%{email}%'))
        
        # query = query.order_by(DepartmentMember.join_date.desc())
        if order == "desc":
            query = query.order_by(desc(getattr(DepartmentMember, sort_by)))
        else:
            query = query.order_by(getattr(DepartmentMember, sort_by))
        
        # members = query.all()
        
        # return members
        
        count = query.count()

        # Handle pagination
        offset = (page - 1) * per_page
        return query.offset(offset).limit(per_page).all(), count
    
    
    @classmethod
    def get_department_roles(
        cls, 
        db: Session, 
        department_id: str,
        page: int,
        per_page: int,
        sort_by: str,
        order: str,
        role_name: Optional[str] = None,
        include_default_roles: bool = True
    ):
        '''Function to get department roles'''
        
        if include_default_roles:
            query = (
                db.query(DepartmentRole).filter(
                    or_(
                        DepartmentRole.department_id == '-1',
                        DepartmentRole.department_id == department_id,
                    )
                )
            )
            
            if role_name:
                query = query.filter(DepartmentRole.role_name.ilike(f'%{role_name}%'))
            
            # query = query.order_by(DepartmentMember.join_date.desc())
            if order == "desc":
                query = query.order_by(desc(getattr(DepartmentRole, sort_by)))
            else:
                query = query.order_by(getattr(DepartmentRole, sort_by))
            
            count = query.count()

            # Handle pagination
            offset = (page - 1) * per_page
            roles = query.offset(offset).limit(per_page).all()
            return roles, count
            
        else:
            query, roles, count = DepartmentRole.fetch_by_field(
                db=db,
                sort_by=sort_by,
                order=order.lower(),
                page=page,
                per_page=per_page,
                search_fields={
                    'role_name': role_name
                },
                department_id=department_id,
            )
            
        return roles, count
    
    @classmethod
    def create_budget(cls, department_id: str, payload:DepartmentBudgetBase, db: Session):
        '''Function to create a department budget'''
        
        # Set default dates
        if not payload.fiscal_period_start and not payload.fiscal_period_end:
            payload.fiscal_period_start = date(payload.fiscal_year, 1, 1)   
    
            if payload.period_type == BudgetPeriodType.ANNUAL:
                payload.fiscal_period_end = date(payload.fiscal_year, 12, 31)
            elif payload.period_type == BudgetPeriodType.QUARTERLY:
                payload.fiscal_period_end = date(payload.fiscal_year, 3, 31)
            elif payload.period_type == BudgetPeriodType.MONTHLY:
                payload.fiscal_period_end = date(payload.fiscal_year, 1, 31)
            else:
                raise HTTPException(400, "Invalid period type")
        
        # Check if there is a start data and no end date
        if payload.fiscal_period_start and not payload.fiscal_period_end:
            
            if payload.fiscal_period_start.year != payload.fiscal_year:
                raise HTTPException(400, "Fiscal year does not match the fiscal period start date")
            
            if payload.period_type == BudgetPeriodType.ANNUAL:
                payload.fiscal_period_end = payload.fiscal_period_start + timedelta(days=364)
            elif payload.period_type == BudgetPeriodType.QUARTERLY:
                payload.fiscal_period_end = payload.fiscal_period_start + timedelta(days=90)
            elif payload.period_type == BudgetPeriodType.MONTHLY:
                payload.fiscal_period_end = payload.fiscal_period_start + timedelta(days=30)
            else:
                raise HTTPException(400, "Invalid period type")
            
        elif payload.fiscal_period_end and not payload.fiscal_period_start:    
            if payload.fiscal_period_end.year != payload.fiscal_year:
                raise HTTPException(400, "Fiscal year does not match the fiscal period end date")
            
            if payload.period_type == BudgetPeriodType.ANNUAL:
                payload.fiscal_period_start = payload.fiscal_period_end - timedelta(days=364)
            elif payload.period_type == BudgetPeriodType.QUARTERLY:
                payload.fiscal_period_start = payload.fiscal_period_end - timedelta(days=90)
            elif payload.period_type == BudgetPeriodType.MONTHLY:
                payload.fiscal_period_start = payload.fiscal_period_end - timedelta(days=30)
            else:
                raise HTTPException(400, "Invalid period type")
        
        if payload.fiscal_period_start > payload.fiscal_period_end:
            raise HTTPException(400, "Fiscal period start date cannot be after end date")
        
        # Create budget
        new_budget = DepartmentBudget.create(
            db=db,
            department_id=department_id,
            **payload.model_dump(exclude_unset=True)
        )
        
        new_budget.unique_id = helpers.generate_unique_id(
            db=db,
            organization_id=new_budget.department.organization_id,
        )
        db.commit()
        db.refresh(new_budget)
        
        logger.info(f"Department budget created with ID: {new_budget.id}")
        
        return new_budget

    
    @classmethod
    def update_budget(cls, db: Session, payload: DepartmentBudgetUpdate, budget_id: str):
        
        budget = DepartmentBudget.fetch_by_id(db, budget_id)
        
        if payload.fiscal_period_start and payload.fiscal_period_end:
            if payload.fiscal_period_start > payload.fiscal_period_end:
                raise HTTPException(400, "Fiscal period start date cannot be after end date")
            
        if payload.currency:
            budget.currency = payload.currency
            
        if payload.fiscal_period_start:
            if payload.fiscal_period_start.year != budget.fiscal_year:
                raise HTTPException(400, "Fiscal year does not match the fiscal period start date")
            
            if payload.fiscal_period_start > budget.fiscal_period_end:
                raise HTTPException(400, "Fiscal period start cannot be greatuer than the budget end date")
            
            budget.fiscal_period_start = payload.fiscal_period_start
            
            if budget.period_type == BudgetPeriodType.ANNUAL:
                budget.fiscal_period_end = payload.fiscal_period_start + timedelta(days=364)
            elif budget.period_type == BudgetPeriodType.QUARTERLY:
                budget.fiscal_period_end = payload.fiscal_period_start + timedelta(days=90)
            elif budget.period_type == BudgetPeriodType.MONTHLY:
                budget.fiscal_period_end = payload.fiscal_period_start + timedelta(days=30)
            
        if payload.fiscal_period_end:
            if payload.fiscal_period_end.year != budget.fiscal_year:
                raise HTTPException(400, "Fiscal year does not match the fiscal period end date")
            
            budget.fiscal_period_end = payload.fiscal_period_end
            
            if budget.period_type == BudgetPeriodType.ANNUAL:
                budget.fiscal_period_start = payload.fiscal_period_end - timedelta(days=364)
            elif budget.period_type == BudgetPeriodType.QUARTERLY:
                budget.fiscal_period_start = payload.fiscal_period_end - timedelta(days=90)
            elif budget.period_type == BudgetPeriodType.MONTHLY:
                budget.fiscal_period_start = payload.fiscal_period_end - timedelta(days=30)
            
        if payload.amount_to_add_from_pending and payload.amount_to_add_from_pending > 0:
            if budget.pending_amount < payload.amount_to_add_from_pending:
                raise HTTPException(400, "Pending amount is less than the amount to add")
            
            # if budget.pending_amount == payload.amount_to_add_from_pending:
            #     budget.pending_amount = 0
            
            budget.pending_amount = float(budget.pending_amount) - payload.amount_to_add_from_pending
            budget.allocated_amount = float(budget.allocated_amount) + payload.amount_to_add_from_pending
            
        if payload.amount_to_remove and payload.amount_to_remove > 0:
            if budget.allocated_amount < payload.amount_to_remove:
                raise HTTPException(400, "Allocated amount is less than the amount to remove")
            
            budget.allocated_amount = float(budget.allocated_amount) - payload.amount_to_remove
            budget.utilized_amount = float(budget.utilized_amount) + payload.amount_to_remove
                
        db.commit()
        
        return budget
