from uuid import uuid4
from fastapi import APIRouter, Depends, Form, HTTPException
from slugify import slugify
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.department import Department
from api.v1.models.user import User
from api.v1.models.project import (
    Project, Milestone, Task, 
    ProjectMember, TaskAssignee
)
from api.v1.schemas.file import FileBase
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.department import DepartmentService
from api.v1.services.organization import OrganizationService
from api.v1.services.file import FileService
from api.v1.services.project import ProjectService
from api.v1.schemas import project as project_schemas
from api.utils.loggers import create_logger


project_router = APIRouter(tags=['Project Management'])
logger = create_logger(__name__)

@project_router.post("/projects", status_code=201, response_model=success_response)
async def create_project(
    payload: project_schemas.ProjectBase = Form(media_type='multipart/form-data'),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new project"""
    
    if (payload.organization_id and payload.department_id) or (not payload.organization_id and not payload.department_id):
        raise HTTPException(400, "Both organization and department id cannot be missing or both be present")
    
    user: User = entity.entity
    
    # generate uuid id because of file upload
    model_id = uuid4().hex
    department = None
    
    if payload.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='project:create',
            organization_id=payload.organization_id
        )

    if payload.department_id:
        department = Department.fetch_by_id(db, payload.department_id)
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='project:create',
            department_id=payload.department_id
        )
        
    if payload.start_date > payload.end_date:
        raise HTTPException(400, 'Start date cannot be greater than end date')
        
    if payload.project_image:
        file = await FileService.upload_file(
            db=db,
            payload=FileBase(
                file=payload.project_image,
                organization_id=payload.organization_id if not payload.department_id else department.organization_id,
                model_name='projects',
                model_id=model_id,
            ),
            allowed_extensions=['jpg', 'png', 'jpeg'],
            add_to_db=False
        )
        payload.logo_url = file['url']
    
    if payload.attachments:
        # TODO: bulk upload files. use celery for this
        await FileService.bulk_upload(
            db=db,
            files=payload.attachments,
            organization_id=payload.organization_id if not payload.department_id else department.organization_id,
            model_name='projects',
            model_id=model_id,
        )
    
    if not payload.logo_url:
        payload.logo_url = helpers.generate_logo_url(payload.name)
    
    if not payload.slug:
        payload.slug = slugify(payload.name)
        
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id if not payload.department_id else department.organization_id,
        )
        
    if payload.additional_info:
        payload.additional_info = helpers.format_additional_info_create(payload.additional_info)
        print(payload.additional_info)
    
    payload.status = payload.status.value
    
    project = Project.create(
        db=db,
        id=model_id,
        creator_id=user.id,
        **payload.model_dump(exclude_unset=True, exclude=['project_image', 'attachments'])
    )
    
    # Create project member
    ProjectMember.create(
        db=db,
        project_id=project.id,
        user_id=user.id,
        role=project_schemas.ProjectMemberRole.owner.value
    )
    
    logger.info(f'Project {project.name} created')

    return success_response(
        message=f"Project created successfully",
        status_code=201,
        data=project.to_dict()
    )


@project_router.get("/projects", status_code=200)
async def get_projects(
    organization_id: str = None,
    department_id: str = None,
    name: str = None,
    slug: str = None,
    status: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all projects"""
    
    if (organization_id and department_id) or (not organization_id and not department_id):
        raise HTTPException(400, "Both organization and department id cannot be missing or both be present")
    
    if organization_id:
        AuthService.belongs_to_organization(
            db=db, entity=entity,
            organization_id=organization_id
        )
    
    if department_id:
        DepartmentService.belongs_to_department(
            db=db, entity=entity,
            department_id=department_id
        )

    query, projects, count = Project.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        organization_id=organization_id,
        department_id=department_id,
        slug=slug,
        status=status
    )
    
    return paginator.build_paginated_response(
        items=[project.to_dict() for project in projects],
        endpoint='/projects',
        page=page,
        size=per_page,
        total=count,
    )


@project_router.get("/projects/{id}", status_code=200, response_model=success_response)
async def get_project_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a project by ID or unique_id in case ID fails."""

    project = Project.fetch_by_id(db, id)
    
    if project.organization_id:
        AuthService.belongs_to_organization(
            db=db, entity=entity,
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.belongs_to_department(
            db=db, entity=entity,
            department_id=project.department_id
        )
        
    return success_response(
        message=f"Fetched project successfully",
        status_code=200,
        data=project.to_dict()
    )


@project_router.patch("/projects/{id}", status_code=200, response_model=success_response)
async def update_project(
    id: str,
    payload: project_schemas.ProjectUpdate = Form(media_type='multipart/form-data'),
    organization_id: str = None,
    department_id: str = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a project"""
    
    if (organization_id and department_id) or (not organization_id and not department_id):
        raise HTTPException(400, "Both organization and department id cannot be missing or both be present")
    
    if organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='project:update',
            organization_id=organization_id
        )

    if department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='project:update',
            department_id=department_id
        )
        
    project = Project.fetch_by_id(db, id)
    
    if payload.start_date and payload.end_date:
        if payload.start_date > payload.end_date:
            raise HTTPException(400, 'Start date cannot be greater than end date')

    if payload.status:
        payload.status = payload.status.value
        
    if payload.project_image:
        file = await FileService.upload_file(
            db=db,
            payload=FileBase(
                file=payload.project_image,
                organization_id=project.organization_id,
                model_name='projects',
                model_id=id,
            ),
            allowed_extensions=['jpg', 'png', 'jpeg'],
            add_to_db=False
        )
        payload.logo_url = file['url']
    
    
    if payload.attachments:
        # TODO: bulk upload files. use celery for this
        await FileService.bulk_upload(
            db=db,
            files=payload.attachments,
            organization_id=project.organization_id,
            model_name='projects',
            model_id=id,
        )
    
    project = Project.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['project_image', 'attachments', 'additional_info'])
    )
    
    if payload.additional_info:
        project.additional_info = helpers.format_additional_info_update(
            additional_info=payload.additional_info,
            model_instance=project
        )
        db.commit()

    return success_response(
        message=f"Project updated successfully",
        status_code=200,
        data=project.to_dict()
    )


@project_router.delete("/projects/{id}", status_code=200, response_model=success_response)
async def delete_project(
    id: str,
    organization_id: str = None,
    department_id: str = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a project"""
    
    if (organization_id and department_id) or (not organization_id and not department_id):
        raise HTTPException(400, "Both organization and department id cannot be missing or both be present")
    
    if organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='project:delete',
            organization_id=organization_id
        )

    if department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='project:delete',
            department_id=department_id
        )

    Project.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )
    

@project_router.post("/projects/{id}/assign-user", status_code=200, response_model=success_response)
async def assign_user_to_project(
    id: str,
    payload: project_schemas.ProjectMemberBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to assign a user to a project"""
    
    project = Project.fetch_by_id(db, id)
    
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='project:assign-member',
            organization_id=project.organization_id
        )

    if project.department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='project:assign-member',
            department_id=project.department_id
        )
    
    # Check if user to be assigned belongs in organization
    org_members, count = OrganizationService.get_organization_members(db, project.organization_id, paginate=False)
    org_members_ids = [member.user.id for member in org_members]
    
    if payload.user_id not in org_members_ids:
        raise HTTPException(400, 'User does not exist in this organization')
    
    payload.role = payload.role.value
    project_member = ProjectMember.create(
        db=db,
        project_id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Project member added successfully",
        status_code=200,
        data=project_member.to_dict()
    )
    

@project_router.patch("/projects/{id}/update-member", status_code=200, response_model=success_response)
async def update_project_member(
    id: str,
    payload: project_schemas.UpdateProjectMember,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a project member"""
    
    project = Project.fetch_by_id(db, id)
    
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='project:update-member',
            organization_id=project.organization_id
        )

    if project.department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='project:update-member',
            department_id=project.department_id
        )
    
    # Check if user to be updated belongs in project
    project_member = ProjectMember.fetch_one_by_field(
        db=db,
        project_id=id,
        user_id=payload.user_id,
        is_active=True
    )
    
    if payload.role:
        project_member.role = payload.role.value
    
    if payload.is_active:
        project_member.is_active = payload.is_active
        
    db.commit()

    logger.info(f'Project member {project_member.id} updated')
    
    return success_response(
        message=f"Project member updated successfully",
        status_code=200,
        data=project_member.to_dict()
    )
    

# ------------------- TASKS --------------------

@project_router.post("/tasks", status_code=201, response_model=success_response)
async def create_task(
    payload: project_schemas.TaskCreate = Form(media_type='multipart/form-data'),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new task"""

    user: User = entity.entity
    department = None
    model_id = uuid4().hex
    
    project = Project.fetch_by_id(db, payload.project_id)
    
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='task:create',
            organization_id=project.organization_id
        )
    
    if project.department_id:
        department = Department.fetch_by_id(db, project.department_id)
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='task:create',
            department_id=project.department_id
        )
        
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['owner', 'admin'],
    #     db=db
    # )

    if payload.due_date:
        if payload.due_date > project.end_date or payload.due_date < project.start_date:
            raise HTTPException(400, 'Due date cannot be greater then project end date or less than project start date')

    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=project.organization_id if not project.department_id else department.organization_id,
        )
        
    if payload.additional_info:
        payload.additional_info = helpers.format_additional_info_create(payload.additional_info)
        print(payload.additional_info)
    
    payload.status = payload.status.value
    
    if payload.attachments:
        # TODO: bulk upload files. use celery for this
        await FileService.bulk_upload(
            db=db,
            files=payload.attachments,
            organization_id=project.organization_id,
            model_name='tasks',
            model_id=model_id,
        )
        
    task = Task.create(
        db=db,
        id=model_id,
        creator_id=user.id,
        **payload.model_dump(exclude_unset=True, exclude=['attackments', 'assignee_ids'])
    )
    
    # Create task assignee
    TaskAssignee.create(
        db=db,
        task_id=task.id,
        user_id=user.id,
    )
    
    if payload.assignee_ids:
        # check if users belong in project
        project_members = project.members
        project_member_user_ids = [member.id for member in project_members]
        
        for user_id in payload.assignee_ids:
            if (user_id in project_member_user_ids) or (user_id not in project_member_user_ids):
                continue
            
            # check if user is already assigned to task
            user_exists_in_task = TaskAssignee.fetch_one_by_field(
                db=db, throw_error=False,
                task_id=task.id,
                user_id=user_id
            )
            
            if user_exists_in_task:
                continue
            
            TaskAssignee.create(
                db=db,
                task_id=task.id,
                user_id=user_id,
            )

    logger.info(f'Task {task.name} created')
    
    return success_response(
        message=f"Task created successfully",
        status_code=201,
        data=task.to_dict()
    )


@project_router.get("/tasks", status_code=200)
async def get_tasks(
    project_id: str,
    name: str = None,
    status: str = None,
    priority: str = None,
    parent_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all tasks"""
    
    project = Project.fetch_by_id(db, project_id)
    
    if project.organization_id:
        AuthService.belongs_to_organization(
            db=db, entity=entity,
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.belongs_to_department(
            db=db, entity=entity,
            department_id=project.department_id
        )
    
    
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['*'],
    #     db=db
    # )

    query, tasks, count = Task.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        project_id=project_id,
        parent_id=parent_id,
        status=status,
        priority=priority
    )
    
    return paginator.build_paginated_response(
        items=[task.to_dict() for task in tasks],
        endpoint='/tasks',
        page=page,
        size=per_page,
        total=count,
    )


@project_router.get("/tasks/{id}", status_code=200, response_model=success_response)
async def get_task_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a task by ID or unique_id in case ID fails."""

    task = Task.fetch_by_id(db, id)
    project = Project.fetch_by_id(db, task.project_id)
    
    if project.organization_id:
        AuthService.belongs_to_organization(
            db=db, entity=entity,
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.belongs_to_department(
            db=db, entity=entity,
            department_id=project.department_id
        )
        
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['*'],
    #     db=db
    # )
    
    return success_response(
        message=f"Fetched task successfully",
        status_code=200,
        data=task.to_dict()
    )


@project_router.patch("/tasks/{id}", status_code=200, response_model=success_response)
async def update_task(
    id: str,
    payload: project_schemas.TaskUpdate = Form(media_type='multipart/form-data'),
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a task"""
    
    task = Task.fetch_by_id(db, id)
    project = Project.fetch_by_id(db, task.project_id)
    
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='task:update',
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='task:update',
            department_id=project.department_id
        )
    
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['owner', 'admin'],
    #     db=db
    # )
        
    if payload.parent_id and payload.parent_id == id:
        raise HTTPException(400, 'Task cannot be it\'s own parent')
    
    if payload.due_date:
        if payload.due_date > project.end_date or payload.due_date < project.start_date:
            raise HTTPException(400, 'Due date cannot be greater then project end date or less than project start date')

    if payload.status:
        payload.status = payload.status.value
        
    if payload.attachments:
        # TODO: bulk upload files. use celery for this
        await FileService.bulk_upload(
            db=db,
            files=payload.attachments,
            organization_id=project.organization_id,
            model_name='tasks',
            model_id=id,
        )
        
    task = Task.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['attachments', 'assignee_ids', 'additional_info'])
    )
    
    if payload.additional_info:
        task.additional_info = helpers.format_additional_info_update(
            additional_info=payload.additional_info,
            model_instance=task
        )  
        db.commit()
    
    if payload.assignee_ids:
        # check if users belong in project
        project_members = project.members
        project_member_user_ids = [member.id for member in project_members]
        
        for user_id in payload.assignee_ids:
            if (user_id in project_member_user_ids) or (user_id not in project_member_user_ids):
                continue
            
            # check if user is already assigned to task
            user_exists_in_task = TaskAssignee.fetch_one_by_field(
                db=db, throw_error=False,
                task_id=task.id,
                user_id=user_id
            )
            
            if user_exists_in_task:
                continue
            
            TaskAssignee.create(
                db=db,
                task_id=task.id,
                user_id=user_id,
            )

    return success_response(
        message=f"Task updated successfully",
        status_code=200,
        data=task.to_dict()
    )


@project_router.delete("/tasks/{id}", status_code=200, response_model=success_response)
async def delete_task(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a task"""
    
    task = Task.fetch_by_id(db, id)
    project = Project.fetch_by_id(db, task.project_id)
    
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='task:delete',
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='task:delete',
            department_id=project.department_id
        )
    
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['owner', 'admin'],
    #     db=db
    # )

    Task.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

@project_router.patch("/tasks/{id}/update-assignee", status_code=200, response_model=success_response)
async def update_task_assignee(
    id: str,
    payload: project_schemas.UpdateTaskAssignee,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a project member"""
    
    task = Task.fetch_by_id(db, id)
    project = Project.fetch_by_id(db, task.project_id)
    
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='task:update-member',
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='task:update-member',
            department_id=project.department_id
        )
    
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['owner', 'admin'],
    #     db=db
    # )
    
    # Check if user to be updated belongs in project
    task_assignee = TaskAssignee.fetch_one_by_field(
        db=db,
        task_id=id,
        user_id=payload.user_id,
        is_active=True
    )
    
    if payload.is_active:
        task_assignee.is_active = payload.is_active
        
    db.commit()

    return success_response(
        message=f"Project member updated successfully",
        status_code=200,
        data=task_assignee.to_dict()
    )

# ------------------- MILESTONES ----------------------

@project_router.post("/milestones", status_code=201, response_model=success_response)
async def create_milestone(
    payload: project_schemas.MilestoneBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new milestone"""
    
    project = Project.fetch_by_id(db, payload.project_id)
    department = None
    
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='milestone:create',
            organization_id=project.organization_id
        )
    
    if project.department_id:
        department = Department.fetch_by_id(db, project.department_id)
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='milestone:create',
            department_id=project.department_id
        )
        
    if payload.due_date:
        if payload.due_date > project.end_date or payload.due_date < project.start_date:
            raise HTTPException(400, 'Due date cannot be greater then project end date or less than project start date')

    
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['owner', 'admin'],
    #     db=db
    # )
        
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=project.organization_id if not project.department_id else department.organization_id,
        )
        
    milestone = Milestone.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Milestone created successfully",
        status_code=201,
        data=milestone.to_dict()
    )


@project_router.get("/milestones", status_code=200)
async def get_milestones(
    project_id: str,
    name: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get all milestones"""
    
    project = Project.fetch_by_id(db, project_id)
    
    if project.organization_id:
        AuthService.belongs_to_organization(
            db=db, entity=entity,
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.belongs_to_department(
            db=db, entity=entity,
            department_id=project.department_id
        )
    
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['*'],
    #     db=db
    # )

    query, milestones, count = Milestone.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        project_id=project_id
    )
    
    return paginator.build_paginated_response(
        items=[milestone.to_dict() for milestone in milestones],
        endpoint='/milestones',
        page=page,
        size=per_page,
        total=count,
    )


@project_router.get("/milestones/{id}", status_code=200, response_model=success_response)
async def get_milestone_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get a milestone by ID or unique_id in case ID fails."""

    milestone = Milestone.fetch_by_id(db, id)
    project = Project.fetch_by_id(db, milestone.project_id)
    
    if project.organization_id:
        AuthService.belongs_to_organization(
            db=db, entity=entity,
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.belongs_to_department(
            db=db, entity=entity,
            department_id=project.department_id
        )
        
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['*'],
    #     db=db
    # )
    
    return success_response(
        message=f"Fetched milestone successfully",
        status_code=200,
        data=milestone.to_dict()
    )


@project_router.patch("/milestones/{id}", status_code=200, response_model=success_response)
async def update_milestone(
    id: str,
    payload: project_schemas.MilestoneUpdate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to update a milestone"""
    
    milestone = Milestone.fetch_by_id(db, id)
    project = Project.fetch_by_id(db, milestone.project_id)
        
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='milestone:update',
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='milestone:update',
            department_id=project.department_id
        )
        
    if payload.due_date:
        if payload.due_date > project.end_date or payload.due_date < project.start_date:
            raise HTTPException(400, 'Due date cannot be greater then project end date or less than project start date')
    
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['owner', 'admin'],
    #     db=db
    # )

    milestone = Milestone.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Milestone updated successfully",
        status_code=200,
        data=milestone.to_dict()
    )


@project_router.delete("/milestones/{id}", status_code=200, response_model=success_response)
async def delete_milestone(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to delete a milestone"""
    
    milestone = Milestone.fetch_by_id(db, id)
    project = Project.fetch_by_id(db, milestone.project_id)
        
    if project.organization_id:
        AuthService.has_org_permission(
            db=db, entity=entity,
            permission='milestone:delete',
            organization_id=project.organization_id
        )
    
    if project.department_id:
        DepartmentService.has_department_permission(
            db=db, entity=entity,
            permission='milestone:delete',
            department_id=project.department_id
        )
    
    # Check project role
    # ProjectService.check_project_role(
    #     project_id=project.id,
    #     entity=entity,
    #     roles=['owner', 'admin'],
    #     db=db
    # )

    Milestone.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )
