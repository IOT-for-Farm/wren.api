from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from slugify import slugify
from sqlalchemy.orm import Session

from api.core.dependencies.email_sending_service import send_email
from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.tag import Tag
from api.v1.models.form import Form, FormResponse, FormTemplate, FormTemplateTag
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.form import FormService
from api.v1.schemas import form as form_schemas
from api.utils.loggers import create_logger
from api.v1.services.organization import OrganizationService
from config import config


form_router = APIRouter( tags=['Form'])
logger = create_logger(__name__)

@form_router.post("/forms", status_code=201, response_model=success_response)
async def create_form(
    payload: form_schemas.FormBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new form"""
    
    AuthService.has_org_permission(
        entity=entity,
        permission='form:create',
        organization_id=payload.organization_id,
        db=db
    )
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(db=db, organization_id=payload.organization_id)

    if not payload.slug:
        payload.slug = f'{payload.unique_id}-{slugify(payload.form_name)}'
    
    # TODO: Update this URL
    if not payload.url:
        payload.url = f"{config('APP_URL')}/forms/{payload.slug}"
        
    if payload.form_template_id:
        form_template = FormTemplate.fetch_by_id(db, payload.form_template_id)
        if form_template.organization_id != payload.organization_id and form_template.organization_id != '-1':
            raise HTTPException(400, "Form template does not exist int this organization")
        
        if payload.fields:
            payload.fields = payload.fields + form_template.fields
        else:
            payload.fields = form_template.fields
    
    form = Form.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f"Form created with id {form.id} and name {form.form_name}")
    
    return success_response(
        message=f"Form created successfully",
        status_code=201,
        data=form.to_dict()
    )
    

@form_router.get("/forms", status_code=200)
async def get_forms(
    organization_id: str,
    form_name: str = None,
    slug: str = None,
    is_active: bool = None,
    form_template_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all forms"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, forms, count = Form.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'form_name': form_name,
        },
        organization_id=organization_id,
        slug=slug,
        is_active=is_active,
        form_template_id=form_template_id,
    )
    
    return paginator.build_paginated_response(
        items=[form.to_dict() for form in forms],
        endpoint='/forms',
        page=page,
        size=per_page,
        total=count,
    )
    

@form_router.get("/forms/{id}", status_code=200, response_model=success_response)
async def get_form_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a form by ID or unique_id in case ID fails."""

    form = Form.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=form.organization_id,
        db=db
    )
    
    return success_response(
        message=f"Fetched form successfully",
        status_code=200,
        data=form.to_dict()
    )


@form_router.patch("/forms/{id}", status_code=200, response_model=success_response)
async def update_form(
    id: str,
    payload: form_schemas.UpdateForm,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a form"""
    
    form = Form.fetch_by_id(db, id)
    
    AuthService.has_org_permission(
        entity=entity,
        permission='form:update',
        organization_id=form.organization_id,
        db=db
    )
    
    if payload.form_template_id:
        form_template = FormTemplate.fetch_by_id(db, payload.form_template_id)
        if form_template.organization_id != form.organization_id and form_template.organization_id == '-1':
            raise HTTPException(400, "Form template does not exist int this organization")
        
        if payload.fields:
            payload.fields = payload.fields + form_template.fields
        else:
            payload.fields = form_template.fields

    updated_form = Form.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Form updated successfully",
        status_code=200,
        data=updated_form.to_dict()
    )


@form_router.delete("/forms/{id}", status_code=200, response_model=success_response)
async def delete_form(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a form"""
    
    form = Form.fetch_by_id(db, id)
    
    AuthService.has_org_permission(
        entity=entity,
        permission='form:delete',
        organization_id=form.organization_id,
        db=db
    )

    Form.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )


# ------------------- FORM TEMPLATES --------------------------
# -------------------------------------------------------------

@form_router.post("/form-templates", status_code=201, response_model=success_response)
async def create_form_template(
    payload: form_schemas.FormTemplateBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new form template"""
    
    AuthService.has_org_permission(
        entity=entity,
        permission='form-template:create',
        organization_id=payload.organization_id,
        db=db
    )
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(db=db, organization_id=payload.organization_id)
    
    form_template = FormTemplate.create(
        db=db,
        **payload.model_dump(exclude_unset=True, exclude=['tag_ids'])
    )
    
    if payload.tag_ids:
        for tag_id in payload.tag_ids:
            # Check that tags exist in the organization
            tag = Tag.fetch_one_by_field(
                db, 
                throw_error=False,
                id=tag_id, 
                organization_id=payload.organization_id
            )
            
            # If tag does not exist, skip
            if not tag:
                continue
            
            # Create template tag association
            FormTemplateTag.create(
                db=db,
                form_template_id=form_template.id,
                tag_id=tag_id
            )

    logger.info(f"Form template created with id {form_template.id} and name {form_template.template_name}")
    
    return success_response(
        message=f"Form template created successfully",
        status_code=201,
        data=form_template.to_dict()
    )
    

@form_router.get("/form-templates", status_code=200)
async def get_form_templates(
    organization_id: str,
    template_name: str = None,
    get_default_templates: bool = False,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all form templates"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, form_templates, count = FormTemplate.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'template_name': template_name,
        },
        organization_id=organization_id if not get_default_templates else '-1'
    )
    
    return paginator.build_paginated_response(
        items=[form_template.to_dict() for form_template in form_templates],
        endpoint='/form-templates',
        page=page,
        size=per_page,
        total=count,
    )


@form_router.get("/form-templates/{id}", status_code=200, response_model=success_response)
async def get_form_template_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a form template by ID or unique_id in case ID fails."""

    form_template = FormTemplate.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=form_template.organization_id,
        db=db
    )
    
    return success_response(
        message=f"Fetched form template successfully",
        status_code=200,
        data=form_template.to_dict()
    )


@form_router.patch("/form-templates/{id}", status_code=200, response_model=success_response)
async def update_form_template(
    id: str,
    payload: form_schemas.UpdateFormTemplate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a form template"""
    
    form_template = FormTemplate.fetch_by_id(db, id)
    
    AuthService.has_org_permission(
        entity=entity,
        permission='form-template:update',
        organization_id=form_template.organization_id,
        db=db
    )

    updated_form_template = FormTemplate.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['tag_ids'])
    )
    
    if payload.tag_ids:
        for tag_id in payload.tag_ids:
            # Check that tags exist in the organization
            tag = Tag.fetch_one_by_field(
                db, 
                throw_error=False,
                id=tag_id, 
                organization_id=form_template.organization_id
            )
            
            # If tag does not exist, skip
            if not tag:
                continue
            
            # Check the tag association
            tag_association = FormTemplateTag.fetch_one_by_field(
                db,
                throw_error=False,
                form_template_id=id,
                tag_id=tag_id
            )
            
            # If tag association exists, skip
            if tag_association:
                continue
            
            FormTemplateTag.create(
                db=db,
                form_template_id=id,
                tag_id=tag_id
            )

    logger.info(f"Form template updated with ID: {form_template.id}")
    
    return success_response(
        message=f"Form updated successfully",
        status_code=200,
        data=updated_form_template.to_dict()
    )


@form_router.delete("/form-templates/{id}", status_code=200, response_model=success_response)
async def delete_form_template(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a form template"""
    
    form_template = FormTemplate.fetch_by_id(db, id)
    
    AuthService.has_org_permission(
        entity=entity,
        permission='form-template:delete',
        organization_id=form_template.organization_id,
        db=db
    )

    FormTemplate.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )



# ------------------- FORM RESPONSE --------------------------
# -------------------------------------------------------------


@form_router.post("/form-responses", status_code=201, response_model=success_response)
async def create_form_response(
    bg_tasks: BackgroundTasks,
    payload: form_schemas.FormResponseBase,
    db: Session=Depends(get_db), 
    # entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new form response"""
    
    form = Form.fetch_by_id(db, payload.form_id)
    
    # Check if form allows for more than one user submission
    if form.allow_more_than_one_user_submission == False:
        # Check if user has submitted before
        existing_form_response = FormResponse.fetch_one_by_field(
            db=db, throw_error=False,
            form_id=payload.form_id,
            email=payload.email,
            status='submitted'
        )
        
        if existing_form_response:
            raise HTTPException(400, 'You cannot make more than one submission')
    
    
    # Check if user has an existing draft response
    existing_draft_response = FormResponse.fetch_one_by_field(
        db=db, throw_error=False,
        form_id=payload.form_id,
        email=payload.email,
        status='draft'
    )
    
    if existing_draft_response:
        raise HTTPException(400, 'You have an existing draft response')
    
    form_response = FormResponse.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )
    
    logger.info(f"Form response created with id {form_response.id}")
    
    # Send email to respondent if possible
    if form_response.send_email_to_respondent and form_response.status == form_schemas.FormResponseStatus.SUBMITTED.value:
        logger.info('Sending email to user')
        bg_tasks.add_task(
            send_email,
            recipients=[form_response.email],
            template_name='form-response.html',
            subject=f"Your response for form `{form.form_name}`",
            template_data={
                'response': {
                    **form_response.to_dict(), 
                    'form': form.to_dict(),
                    'submission_date': form_response.updated_at.strftime('%d %B %Y at %I:%M%p')
                }
            },
        )
    
    # Send email to organization members
    if form.receive_response_email_notifications and form_response.status == form_schemas.FormResponseStatus.SUBMITTED.value:
        logger.info('Sending email to organization')
        OrganizationService.send_email_to_organization(
            db=db,
            bg_tasks=bg_tasks,
            organization_id=form.organization_id,
            template_name='form-response.html',
            subject=f"Response to form `{form.form_name}` submitted",
            context={
                'response': {
                    **form_response.to_dict(), 
                    'form': form.to_dict(),
                    'submission_date': form_response.updated_at.strftime('%d %B %Y at %I:%M%p')
                }
            },
        )
        
    return success_response(
        message=f"Form response created successfully",
        status_code=201,
        data=form_response.to_dict()
    )


@form_router.get("/form-responses", status_code=200)
async def get_form_responses(
    form_id: str,
    organization_id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all form responses"""
    
    # get form
    form = Form.fetch_by_id(db, form_id)
    
    if form.organization_id != organization_id:
        raise HTTPException(400, 'Form does not belong in this organization')
    
    AuthService.has_org_permission(
        entity=entity,
        permission="form:view-responses",
        organization_id=organization_id,
        db=db
    )

    query, form_responses, count = FormResponse.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        form_id=form_id,
    )
    
    return paginator.build_paginated_response(
        items=[form_response.to_dict() for form_response in form_responses],
        endpoint='/form-responses',
        page=page,
        size=per_page,
        total=count,
    )
    

@form_router.get("/form-responses/pre-response-check", status_code=200, response_model=success_response)
async def user_pre_response_check(
    form_id: str,
    email: str,
    status: str,
    db: Session=Depends(get_db), 
):
    """Endpoint to check if a user response exists by the status. If a user has a submitted response
    and the form does not allow for more than one response per user, this endpoint blocks the request
    from happening. It is best to use this endpoint before using the crate response endpoint or use it in
    the frontend of the app to prevent the form page from loading up if there is a submitted response for the user.
    """
    
    form = Form.fetch_by_id(db, form_id)
    
    response = FormResponse.fetch_one_by_field(
        db=db,
        form_id=form_id,
        email=email,
        status=status
    )
    
    if response and status == 'submitted' and form.allow_more_than_one_user_submission == False:
        raise HTTPException(400, 'You cannot respond more than once')
    
    return success_response(
        message=f"Form response fetched successfully",
        status_code=200,
        data=response.to_dict()
    )
    

@form_router.patch("/form-responses/{id}", status_code=200, response_model=success_response)
async def update_form_response(
    id: str,
    bg_tasks: BackgroundTasks,
    payload: form_schemas.UpdateFormResponse,
    db: Session=Depends(get_db), 
    # entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a form response"""
    
    response = FormResponse.fetch_by_id(db, id)
    
    if response.status == form_schemas.FormResponseStatus.SUBMITTED.value:
        raise HTTPException(400, 'Cannot update a submitted form response')
    
    form_response = FormResponse.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    logger.info(f"Form response updated with id {form_response.id}")
    
    if form_response.send_email_to_respondent and form_response.status == form_schemas.FormResponseStatus.SUBMITTED.value:
        bg_tasks.add_task(
            send_email,
            recipients=[form_response.email],
            template_name='form-response.html',
            subject=f"Your response for form `{form_response.form.form_name}`",
            template_data={
                'response': {**form_response.to_dict(), 'submission_date': form_response.updated_at.strftime('%d %B %Y at %I:%M%p')}
            },
        )
        
    # Send email to organization members
    if form_response.form.receive_response_email_notifications and form_response.status == form_schemas.FormResponseStatus.SUBMITTED.value:
        OrganizationService.send_email_to_organization(
            db=db,
            bg_tasks=bg_tasks,
            organization_id=form_response.form.organization_id,
            template_name='form-response.html',
            subject=f"Response to form `{form_response.form.form_name}` submitted",
            context={
                'response': {**form_response.to_dict(), 'submission_date': form_response.updated_at.strftime('%d %B %Y at %I:%M%p')}
            },
        )
    
    return success_response(
        message=f"Form response updated successfully",
        status_code=200,
        data=form_response.to_dict()
    )
    

@form_router.get("/form-responses/{id}", status_code=200, response_model=success_response)
async def get_form_response(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a form response"""
    
    response = FormResponse.fetch_by_id(db, id)
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=response.form.organization_id,
        permission="form:view-responses",
        db=db
    )
    
    return success_response(
        message=f"Form response fetched successfully",
        status_code=200,
        data=response.to_dict()
    )
