from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.organization import OrganizationMember
from api.v1.models.user import User
from api.v1.models.department import BudgetAdjustment, Department, DepartmentBudget, DepartmentMember, DepartmentRole
from api.v1.services.auth import AuthService
from api.v1.services.department import DepartmentService
from api.v1.schemas import department as department_schemas
from api.utils.loggers import create_logger
from api.v1.schemas.auth import AuthenticatedEntity


department_router = APIRouter(prefix='/departments', tags=['Department'])
logger = create_logger(__name__)

@department_router.post("", status_code=201, response_model=success_response)
async def create_department(
    payload: department_schemas.DepartmentBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new department"""
    
    current_user: User = entity.entity
    AuthService.has_org_permission(
        entity=entity,
        organization_id=payload.organization_id,
        permission='department:create',
        db=db
    )

    if payload.additional_info:
        payload.additional_info = helpers.format_additional_info_create(payload.additional_info)
        print(payload.additional_info)
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(db=db, organization_id=payload.organization_id)
        
    department = Department.create(
        db=db,
        creator_id=current_user.id,
        **payload.model_dump(exclude_unset=True)
    )
    
    # Get role of Department Head
    role = DepartmentRole.fetch_one_by_field(
        db=db, 
        department_id='-1',
        role_name='Department Head'
    )
    
    # Add user to department as department head
    DepartmentMember.create(
        db=db,
        department_id=department.id,
        user_id=current_user.id,
        role_id=role.id
    )

    logger.info(f"Department created by {current_user.email} with ID: {department.id}")
    
    return success_response(
        message=f"Department created successfully",
        status_code=200,
        data=department.to_dict()
    )


@department_router.get("", status_code=200)
async def get_departments(
    organization_id: str,
    name: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    parent_id: Optional[str] = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all departments for an organization"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, departments, count = Department.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        organization_id=organization_id,
        parent_id=parent_id
    )
    
    return paginator.build_paginated_response(
        items=[department.to_dict() for department in departments],
        endpoint='/departments',
        page=page,
        size=per_page,
        total=count,
    )


@department_router.get("/{id}", status_code=200, response_model=success_response)
async def get_department_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a department by ID or unique_id in case ID fails."""
    
    DepartmentService.belongs_to_department(
        entity=entity,
        department_id=id,
        db=db
    )
    
    department = Department.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched department successfully",
        status_code=200,
        data=department.to_dict()
    )


@department_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_department(
    id: str,
    organization_id: str,
    payload: department_schemas.UpdateDepartment,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a department"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='department:update',
        db=db
    )

    department = Department.fetch_by_id(db=db, id=id)
    
    if payload.parent_id and payload.parent_id == id:
        raise HTTPException(400, "Department cannot be its own parent")
    
    if payload.parent_id:
        parent_department = Department.fetch_by_id(db=db, id=payload.parent_id)
        if parent_department.organization_id != organization_id:
            raise HTTPException(400, "Parent department does not belong to this organization")
    
    if payload.name:
        department.name = payload.name
        
    if payload.parent_id:
        department.parent_id = payload.parent_id
        
    if payload.unique_id:
        department.unique_id = payload.unique_id
    
    if payload.additional_info:
        department.additional_info = helpers.format_additional_info_update(
            additional_info=payload.additional_info,
            model_instance=department,
            keys_to_remove=payload.additional_info_keys_to_remove
        )
        
    db.commit()
    db.refresh(department)

    return success_response(
        message=f"Department updated successfully",
        status_code=200,
        data=department.to_dict()
    )


@department_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_department(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a department"""

    AuthService.has_org_permission(
        entity=entity,
        organization_id=organization_id,
        permission='department:delete',
        db=db
    )
    
    Department.soft_delete(db, id)
    
    # Delete the department children as well
    query, children, count = Department.fetch_by_field(
        db=db,
        parent_id=id
    )
    for child in children:
        Department.soft_delete(db, child.id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )
    

@department_router.post("/{id}/roles", status_code=201, response_model=success_response)
async def create_department_role(
    id: str,
    payload: department_schemas.DepartmentRoleBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new department role"""
    
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=id,
        permission='department:create-role',
        db=db
    )

    role = DepartmentRole.create(
        db=db,
        department_id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Department role created successfully",
        status_code=200,
        data=role.to_dict()
    )
    
@department_router.get("{id}/roles", status_code=200)
async def get_department_roles(
    id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    include_default_roles: bool = True,
    role_name: Optional[str] = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all department roles"""
    
    DepartmentService.belongs_to_department(
        entity=entity,
        department_id=id,
        db=db
    )

    roles, count = DepartmentService.get_department_roles(
        db=db,
        department_id=id,
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        role_name=role_name,
        include_default_roles=include_default_roles
    )
        
    return paginator.build_paginated_response(
        items=[role.to_dict() for role in roles],
        endpoint=f'/departments/{id}/roles',
        page=page,
        size=per_page,
        total=count,
    )


@department_router.patch("/roles/{role_id}", status_code=200, response_model=success_response)
async def update_department_role(
    role_id: str,
    payload: department_schemas.DepartmentRoleUpdate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a department role"""
    
    # Get role
    role = DepartmentRole.fetch_by_id(db, role_id)
    
    # No need to expicitly check if role is in department as this function
    # checks if the logged  in entity belongs to the department to even make changes to it
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=role.department_id,
        permission='department:update-role',
        db=db
    )

    if payload.permissions:
        current_role_permissions = list(role.permissions)
        payload_permissions = payload.permissions

        # Merge both lists and remove duplicates
        updated_permissions = list(set(current_role_permissions + payload_permissions))
        payload.permissions = updated_permissions
        
    role = DepartmentRole.update(
        db=db,
        id=role.id,
        **payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        message=f"Role `{role.role_name}` updated successfully",
        status_code=200,
        data=role.to_dict()
    )
    

@department_router.delete("/roles/{role_id}", status_code=200, response_model=success_response)
async def delete_department_role(
    role_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a department role"""
    
    # Get role
    role = DepartmentRole.fetch_by_id(db, role_id)
    
    # No need to expicitly check if role is in department as this function
    # checks if the logged  in entity belongs to the department to even make changes to it
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=role.department_id,
        permission='department:delete-role',
        db=db
    )

    DepartmentRole.soft_delete(db, role.id)
    
    return success_response(
        message=f"Role deleted successfully",
        status_code=200
    )
    

@department_router.get("/{id}/members", status_code=200)
async def get_department_members(
    id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'join_date',
    order: str = 'desc',
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get department members"""
    
    DepartmentService.belongs_to_department(
        entity=entity,
        department_id=id,
        db=db
    )

    department_members, count = DepartmentService.get_department_members(
        db=db, 
        department_id=id,
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        full_name=full_name,
        email=email
    )
    
    return paginator.build_paginated_response(
        items=[member.to_dict() for member in department_members],
        endpoint=f'/departments/{id}/members',
        page=page,
        size=per_page,
        total=count
    )
    

@department_router.post("/{id}/members", status_code=200, response_model=success_response)
async def add_user_to_department(
    id: str,
    payload: department_schemas.AddMemberToDepartment,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to add a user to a department"""
    
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=id,
        permission='department:add-member',
        db=db
    )
    
    # Check if user exists in organization
    department = Department.fetch_by_id(db, id)
    
    OrganizationMember.fetch_one_by_field(
        db=db,
        user_id=payload.user_id,
        organization_id=department.organization_id
    )

    # Check if role exists in department
    DepartmentService.role_exists_in_department(db, id, payload.role_id)
    
    # Check if user exists in department
    department_member = DepartmentMember.fetch_one_by_field(
        db=db, throw_error=False,
        department_id=id,
        user_id=payload.user_id
    )
    
    if department_member:
        raise HTTPException(400, 'User already exists in this department')
    
    new_department_member = DepartmentMember.create(
        db=db,
        department_id=department.id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Department member added successfully",
        status_code=200,
        data=new_department_member.to_dict()
    )
    
    
@department_router.delete("/{id}/members", status_code=200, response_model=success_response)
async def remove_user_from_department(
    id: str,
    payload: department_schemas.RemoveMemberFromDepartment,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to remove a user from a department"""
    
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=id,
        permission='department:remove-member',
        db=db
    )

    department_member = DepartmentMember.fetch_one_by_field(
        db=db,
        user_id=payload.user_id,
        department_id=id
    )
    
    DepartmentMember.soft_delete(
        db=db,
        id=department_member.id
    )

    return success_response(
        message=f"Department member removed successfully",
        status_code=200
    )
    

@department_router.patch("/{id}/members", status_code=200, response_model=success_response)
async def assign_role_to_department_member(
    id: str,
    payload: department_schemas.AddMemberToDepartment,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to assign a role to a user in the department"""
    
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=id,
        permission='department:assign-role',
        db=db
    )
    
    # Check if role exists in department
    DepartmentService.role_exists_in_department(db, id, payload.role_id)
    
    department_member = DepartmentMember.fetch_one_by_field(
        db=db,
        user_id=payload.user_id,
        department_id=id
    )

    updated_member = DepartmentMember.update(
        db=db,
        id=department_member.id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Department member role updated successfully",
        status_code=200,
        data=updated_member.to_dict()
    )
    

@department_router.post('{id}/budgets', status_code=201, response_model=success_response)
async def create_department_budget(
    id: str,
    payload: department_schemas.DepartmentBudgetBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new department budget"""
    
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=id,
        permission='department:create-budget',
        db=db
    )
    
    new_budget = DepartmentService.create_budget(
        db=db,
        department_id=id,
        payload=payload
    )

    return success_response(
        message=f"Department budget created successfully",
        status_code=200,
        data=new_budget.to_dict()
    )


@department_router.get('{id}/budgets', status_code=200)
async def get_department_budgets(
    id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all department budgets"""
    
    DepartmentService.belongs_to_department(
        entity=entity,
        department_id=id,
        db=db
    )

    query, budgets, count = DepartmentBudget.fetch_by_field(
        db=db,
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        department_id=id,
    )
    
    return paginator.build_paginated_response(
        items=[budget.to_dict() for budget in budgets],
        endpoint=f'/departments/{id}/budgets',
        page=page,
        size=per_page,
        total=count
    )
    

@department_router.get('/budgets/{budget_id}', status_code=200, response_model=success_response)
async def get_department_budget_by_id(
    budget_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a department budget by ID or unique_id in case ID fails."""
    
    budget = DepartmentBudget.fetch_by_id(db, budget_id)
    
    # Check if user belongs to department
    DepartmentService.belongs_to_department(
        entity=entity,
        department_id=budget.department_id,
        db=db
    )
    
    return success_response(
        message=f"Fetched department budget successfully",
        status_code=200,
        data=budget.to_dict()
    )
    

@department_router.patch('/budgets/{budget_id}', status_code=200, response_model=success_response)
async def update_department_budget(
    budget_id: str,
    payload: department_schemas.DepartmentBudgetUpdate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a department budget"""
    
    budget = DepartmentBudget.fetch_by_id(db, budget_id)
    
    # Check if user belongs to department
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=budget.department_id,
        permission="department:update-budget",
        db=db
    )
    
    updated_budget = DepartmentService.update_budget(
        db=db,
        budget_id=budget.id,
        payload=payload
    )
    
    logger.info(f"Department budget updated by with ID: {updated_budget.id}")
    
    return success_response(
        message=f"Department budget updated successfully",
        status_code=200,
        data=updated_budget.to_dict()
    )
    

@department_router.post("/budgets/{budget_id}/adjustments", status_code=201, response_model=success_response)
async def request_budget_adjustment(
    budget_id: str,
    payload: department_schemas.BudgetAdjustmentBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new budget adjustment"""
    
    current_user: User = entity.entity
    budget = DepartmentBudget.fetch_by_id(db, budget_id)
    
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=budget.department_id,
        permission='department:request-funds',
        db=db
    )
    
    # Create budget adjustment
    new_budget_adjustment = BudgetAdjustment.create(
        db=db,
        budget_id=budget.id,
        requester_id=current_user.id,
        **payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        message=f"Department budget adjustment created successfully",
        status_code=200,
        data=new_budget_adjustment.to_dict()
    )
    

@department_router.get("/budgets/{budget_id}/adjustments", status_code=200)
async def get_budget_adjustment_history(
    budget_id: str,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all budget adjustments"""
    
    budget = DepartmentBudget.fetch_by_id(db, budget_id)
    
    DepartmentService.belongs_to_department(
        entity=entity,
        department_id=budget.department_id,
        db=db
    )

    query, adjustments, count = BudgetAdjustment.fetch_by_field(
        db=db,
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'status': status,
        },
        budget_id=budget.id,
    )
    
    return paginator.build_paginated_response(
        items=[adjustment.to_dict() for adjustment in adjustments],
        endpoint=f'/departments/budgets/{budget.id}/adjustments',
        page=page,
        size=per_page,
        total=count
    )


@department_router.patch("/budgets/{budget_id}/adjustments/{adjustment_id}", status_code=200, response_model=success_response)
async def approve_or_reject_budget_adjustment(
    budget_id: str,
    adjustment_id: str,
    payload: department_schemas.BudgetAdjustmentUpdate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to approve or reject a budget adjustment"""
    
    current_user: User = entity.entity
    budget = DepartmentBudget.fetch_by_id(db, budget_id)
    
    DepartmentService.has_department_permission(
        entity=entity,
        department_id=budget.department_id,
        permission='department:approve-funds',
        db=db
    )
    
    # Get budget adjustment
    budget_adjustment = BudgetAdjustment.fetch_by_id(db, adjustment_id)
    
    budget_adjustment.status = payload.status.value        
    budget_adjustment.approver_id = current_user.id
    
    # Add or subtract the amount from the budget
    if payload.status.value == 'approved' and budget_adjustment.amount > 0:
        # Add approved funds to pending account as it can be withdrawn later on
        budget.pending_amount += budget_adjustment.amount
    
    if payload.status.value == 'approved' and budget_adjustment.amount < 0:
        # Remove amount from budget allocated amount
        # +ve sign is used as the amount will be -ve in value (+ve * -ve = -ve)
        budget.allocated_amount += budget_adjustment.amount
        
    db.commit()
    
    return success_response(
        message=f"Department budget adjustment approved successfully" if budget_adjustment.status == 'approved' else "Department budget adjustment rejected",
        status_code=200,
        data=budget_adjustment.to_dict()
    )


@department_router.get("/budgets/{budget_id}/adjustments/{adjustment_id}", status_code=200, response_model=success_response)
async def get_budget_adjustment_details(
    budget_id: str,
    adjustment_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to approve or reject a budget adjustment"""
    
    budget = DepartmentBudget.fetch_by_id(db, budget_id)
    
    DepartmentService.belongs_to_department(
        entity=entity,
        department_id=budget.department_id,
        db=db
    )
    
    # Get budget adjustment
    budget_adjustment = BudgetAdjustment.fetch_by_id(db, adjustment_id)
    
    return success_response(
        message=f"Department budget adjustment details fetched successfully",
        status_code=200,
        data=budget_adjustment.to_dict()
    )
