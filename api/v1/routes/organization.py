from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator
from api.utils.responses import success_response
from api.utils.settings import settings
from api.utils.telex_notification import TelexNotification
from api.v1.models.contact_info import ContactInfo
from api.v1.models.location import Location
from api.v1.models.user import User
from api.v1.models.organization import Organization, OrganizationInvite, OrganizationMember, OrganizationRole
from api.v1.services.auth import AuthService
from api.v1.services.organization import OrganizationService
from api.v1.schemas import organization as organization_schemas
from api.v1.schemas import contact_info as contact_info_schemas
from api.v1.schemas import location as location_schemas
from api.utils.loggers import create_logger
from api.v1.schemas.auth import AuthenticatedEntity


organization_router = APIRouter(prefix='/organizations', tags=['Organization'])
logger = create_logger(__name__)

@organization_router.post("", status_code=201, response_model=success_response)
async def create_organization(
    payload: organization_schemas.CreateOrganization,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to create a new organization

    Args:
        payload: Payload for creating a new organization.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    user: User = entity.entity
    organization = OrganizationService.create(
        db=db,
        user_id=user.id,
        payload=payload
    )
    
    TelexNotification(webhook_id="01964195-9203-797f-9665-ce8bcf17e2ac").send_notification(
        event_name='Organization Created',
        message=f'New organization created.\n\nDetails:\nName: {organization.name}\nType: {organization.business_type}\nCurrency code: {organization.currency}\nEmail: {payload.email}',
        status='success',
        username='Organizations'
    )

    return success_response(
        message=f"Organization created successfully",
        status_code=200,
        data=organization.to_dict()
    )


@organization_router.get("", status_code=200)
async def get_organizations(
    name: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_superuser)
):
    """Endpoint to get all organizations

    Args:
        name (str, optional): Search query. Defaults to None.
        page (int, optional): Page number. Defaults to 1.
        per_page (int, optional): Number of items per page. Defaults to 10.
        sort_by (str, optional): Field to sort by. Defaults to 'created_at'.
        order (str, optional): Order of sorting. Defaults to 'desc'.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """

    query, organizations, count = Organization.all(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
    )
    
    return paginator.build_paginated_response(
        items=[organization.to_dict() for organization in organizations],
        endpoint='/organizations',
        page=page,
        size=per_page,
        total=count,
    )


@organization_router.get("/me", status_code=200, response_model=success_response)
async def get_user_organizations(
    name: str = None,
    # page: int = 1,
    # per_page: int = 10,
    # sort_by: str = 'created_at',
    # order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to get the current user organizations
    Args:
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    user: User = entity.entity
    organizations = OrganizationService.get_user_organizations(db, user.id, name)
    
    return success_response(
        status_code=200,
        message='User organizations fetched successfully',
        # data=[organization.to_dict() for organization in organizations],
        data=organizations,
    )
    

@organization_router.post("/{id}/invites", status_code=200, response_model=success_response)
async def invite_to_organization(
    id: str,
    payload: organization_schemas.InviteUser,
    bg_tasks: BackgroundTasks,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to invite a user to an organization"""
    
    user: User = entity.entity
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='organization:invite-user',
        db=db
    )

    invite = OrganizationService.invite_user(
        db=db,
        bg_tasks=bg_tasks,
        payload=payload,
        inviter_id=user.id,
        organization_id=id
    )
    
    return success_response(
        message=f"Invite sent to {payload.email} successfully",
        status_code=200,
        data=invite.to_dict()
    )
    

@organization_router.get("/{id}/invites", status_code=200)
async def get_organization_invites(
    id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    status: Optional[str]=None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to invite a user to an organization"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=id,
        db=db
    )

    query, invites, count = OrganizationInvite.fetch_by_field(
        db=db,
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'status': status,
        },
        organization_id=id
    )
    
    return paginator.build_paginated_response(
        items=[invite.to_dict() for invite in invites],
        endpoint=f'/organizations/{id}/invites',
        page=page,
        size=per_page,
        total=count,
    )
    

@organization_router.get("/invites/respond", status_code=200, response_model=success_response)
async def accept_or_decline_invitation(
    bg_tasks: BackgroundTasks,
    token: str,
    status: str = 'accepted',  # or declined
    db: Session=Depends(get_db), 
):
    """Endpoint for a user to accept or decline an invitation"""
    
    if status not in ['accepted', 'declined']:
        raise HTTPException(400, f'Expecting status of accepted or declined. Got {status} ')

    OrganizationService.update_invitation(
        db=db,
        status=status,
        bg_tasks=bg_tasks,
        token=token
    )
    
    return success_response(
        message=f"Invite {status}",
        status_code=200
    )
    

@organization_router.get("/invites/revoke", status_code=200, response_model=success_response)
async def revoke_invite(
    bg_tasks: BackgroundTasks,
    invite_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to revoke an invitation"""
    
    invite = OrganizationInvite.fetch_by_id(db, invite_id)
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=invite.organization_id,
        permission='organization:revoke-invite',
        db=db
    )

    OrganizationService.update_invitation(
        db=db,
        status='revoked',
        bg_tasks=bg_tasks,
        invite_id=invite_id
    )
    
    return success_response(
        message=f"Invite revoked",
        status_code=200,
    )


@organization_router.get("/slug/{slug}", status_code=200, response_model=success_response)
async def get_organization_by_slug(
    slug: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a organization by slug
    Args:
        slug (str): slug of the organization to retrieve.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    organization = Organization.fetch_one_by_field(db, slug=slug)
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization.id,
        db=db
    )
    
    current_logged_in_member = None
    if entity.type == 'user':
        current_logged_in_member = OrganizationMember.fetch_one_by_field(
            db=db,
            user_id=entity.entity.id,
            organization_id=organization.id
        )
        
    return success_response(
        message=f"Fetched organization successfully",
        status_code=200,
        data={
            **organization.to_dict(),
            "current_user_role": current_logged_in_member.role.role_name if current_logged_in_member else None
        }
    )
    

@organization_router.get("/{id}", status_code=200, response_model=success_response)
async def get_organization_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a organization by ID or unique_id in case ID fails.
    Args:
        id (str): ID of the organization to retrieve.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=id,
        db=db
    )

    organization = Organization.fetch_by_id(db, id)
    
    current_logged_in_member = None
    if entity.type == 'user':
        current_logged_in_member = OrganizationMember.fetch_one_by_field(
            db=db,
            user_id=entity.entity.id,
            organization_id=organization.id
        )
    
    return success_response(
        message=f"Fetched organization successfully",
        status_code=200,
        data={
            **organization.to_dict(),
            "current_user_role": current_logged_in_member.role.role_name if current_logged_in_member else None
        }
    )


@organization_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_organization(
    id: str,
    payload: organization_schemas.UpdateOrganization,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a organization

    Args:
        id (str): ID of the organization to update.
        payload: Payload for updating the organization.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (User, optional): Current logged in user for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='organization:update',
        db=db
    )

    organization = Organization.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Organization updated successfully",
        status_code=200,
        data=organization.to_dict()
    )


@organization_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_organization(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a organization

    Args:
        id (str): ID of the organization to delete.
        db (Session, optional): DB session. Defaults to Depends(get_db).
        entity (AuthenticatedEntity, optional): Current logged in user or apikey for authentication. Defaults to Depends(AuthService.get_current_entity).
    """
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='organization:delete',
        db=db
    )

    Organization.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
        data={"id": id}
    )


@organization_router.get("/{id}/members", status_code=200)
async def get_organization_members(
    id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'join_date',
    order: str = 'desc',
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get organization members"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='organization:view-members',
        db=db
    )

    org_members, count = OrganizationService.get_organization_members(
        db=db, 
        organization_id=id,
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        full_name=full_name,
        email=email
    )
    
    return paginator.build_paginated_response(
        items=[org_member.to_dict() for org_member in org_members],
        endpoint=f'/organizations/{id}/members',
        page=page,
        size=per_page,
        total=count
    )


@organization_router.post("/{id}/members/toggle-active", status_code=200, response_model=success_response)
async def activate_or_deactivate_member(
    id: str,
    payload: organization_schemas.ActivateOrDeactivateMember,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to activate or deactivate organization members"""
    
    current_user: User = entity.entity
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='organization:manage-members',
        db=db
    )
    
    if current_user.id == payload.user_id:
        raise HTTPException(400, 'You cannot update your activity status')

    org_member = OrganizationMember.fetch_one_by_field(
        db=db, organization_id=id,
        user_id=payload.user_id
    )
    
    if org_member.role.role_name == 'Owner':
        raise HTTPException(400, 'You cannot update active state of the owner of the organization')
    
    updated_member = OrganizationMember.update(
        db=db, id=org_member.id,
        is_active=not org_member.is_active
    )
    
    return success_response(
        message=f"Organization member activated" if updated_member.is_active else "Organization member deactivated",
        status_code=200
    )


@organization_router.delete("/{id}/members/remove-member", status_code=200, response_model=success_response)
async def remove_member_from_organization(
    id: str,
    payload: organization_schemas.ActivateOrDeactivateMember,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    """Endpoint to remove an organization member"""
    
    current_user: User = entity.entity
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='organization:manage-members',
        db=db
    )
    
    if current_user.id == payload.user_id:
        raise HTTPException(400, 'You cannot remove yourself from an organization')

    org_member = OrganizationMember.fetch_one_by_field(
        db=db, organization_id=id,
        user_id=payload.user_id
    )
    
    if org_member.role.role_name == 'Owner':
        raise HTTPException(400, 'You cannot remove the owner of the organization')
    
    OrganizationMember.soft_delete(db=db, id=org_member.id)
    
    return success_response(
        message=f"Organization member removed",
        status_code=200
    )


@organization_router.post("{id}/roles", status_code=201, response_model=success_response)
async def create_organization_role(
    id: str,
    payload: organization_schemas.CreateRole,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create an organization role"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='role:create',
        db=db
    )

    payload.role_name = payload.role_name.lower()  # convert role name to lowercase for consistency
    role = OrganizationRole.create(
        db=db,
        organization_id=id,
        **payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        message=f"New role `{role.role_name}` created successfully",
        status_code=201,
        data=role.to_dict()
    )
    

@organization_router.get("{id}/roles", status_code=200)
async def get_organization_roles(
    id: str,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    include_default_roles: bool = True,
    role_name: Optional[str] = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all organization roles"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=id,
        db=db
    )

    roles, count = OrganizationService.get_organization_roles(
        db=db,
        organization_id=id,
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        role_name=role_name,
        include_default_roles=include_default_roles
    )
        
    return paginator.build_paginated_response(
        items=[role.to_dict() for role in roles],
        endpoint=f'/organizations/{id}/roles',
        page=page,
        size=per_page,
        total=count,
    )


@organization_router.patch("/roles/{role_id}", status_code=200, response_model=success_response)
async def update_organization_role(
    role_id: str,
    payload: organization_schemas.UpdateRole,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update an organization role"""
    
    # Get role
    role = OrganizationRole.fetch_by_id(db, role_id)
    
    # No need to expicitly check if role is in organization as this function
    # checks if the logged  in entity belongs to the organization to even make changes to it
    AuthService.has_org_permission(
        entity=entity,
        organization_id=role.organization_id,
        permission='role:update',
        db=db
    )
    
    if payload.permissions:
        current_role_permissions = list(role.permissions)
        payload_permissions = payload.permissions

        # Merge both lists and remove duplicates
        updated_permissions = list(set(current_role_permissions + payload_permissions))
        payload.permissions = updated_permissions

    role = OrganizationRole.update(
        db=db,
        id=role.id,
        **payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        message=f"Role `{role.role_name}` updated successfully",
        status_code=200,
        data=role.to_dict()
    )
    

@organization_router.delete("/roles/{role_id}", status_code=200, response_model=success_response)
async def delete_organization_role(
    role_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete an organization role"""
    
    # Get role
    role = OrganizationRole.fetch_by_id(db, role_id)
    
    # No need to expicitly check if role is in organization as this function
    # checks if the logged  in entity belongs to the organization to even make changes to it
    AuthService.has_org_permission(
        entity=entity,
        organization_id=role.organization_id,
        permission='role:delete',
        db=db
    )

    OrganizationRole.soft_delete(db, role.id)
    
    return success_response(
        message=f"Role deleted successfully",
        status_code=200
    )


@organization_router.post("/assign-role", status_code=200, response_model=success_response)
async def assign_role_to_organization_member(
    payload: organization_schemas.AssignRole,
    db: Session=Depends(get_db),
    entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity)
):
    '''Endpoint to assign a role to a user in an organization'''
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=payload.organization_id,
        permission='organization:assign-role',
        db=db
    )
    
    # Check if role exists in organization
    OrganizationService.role_exists_in_org(db, payload.organization_id, payload.role_id)
    
    # get org member
    org_member = OrganizationMember.fetch_one_by_field(
        db=db, organization_id=payload.organization_id,
        user_id=payload.user_id
    )
    
    # Update user role
    updated_member = OrganizationMember.update(
        db=db, id=org_member.id,
        role_id=payload.role_id
    )
    
    return success_response(
        message=f"Role `{updated_member.role.role_name}` assigned to user successfully",
        status_code=200,
        data=updated_member.to_dict()
    )


@organization_router.post("{id}/contact-infos", status_code=201, response_model=success_response)
async def create_organization_contact_info(
    id: str,
    payload: contact_info_schemas.ContactInfoBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to add a new contact information to an organization"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='contact_info:create',
        db=db
    )

    payload.model_name = 'organizations'
    payload.model_id = id
    contact_info = ContactInfo.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        message=f"New contact info created successfully",
        status_code=201,
        data=contact_info.to_dict()
    )
    

@organization_router.get("{id}/contact-infos", status_code=200, response_model=success_response)
async def get_organization_contact_infos(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all organization contact information"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=id,
        db=db
    )

    query, contact_infos, count = ContactInfo.fetch_by_field(
        db=db,
        model_name='organizations',
        model_id=id
    )
        
    return success_response(
        message=f"Contact infos fetched successfully",
        status_code=201,
        data=[contact_info.to_dict() for contact_info in contact_infos]
    )


@organization_router.patch("/contact-infos/{info_id}", status_code=200, response_model=success_response)
async def update_organization_contact_info(
    info_id: str,
    payload: contact_info_schemas.UpdateContactInfo,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update an organization contact information"""
    
    # Get contact info
    contact_info = ContactInfo.fetch_by_id(db, info_id)
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=contact_info.model_id,
        permission='contact_info:update',
        db=db
    )

    contact_info = ContactInfo.update(
        db=db,
        id=contact_info.id,
        **payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        message=f"Contact info updated successfully",
        status_code=200,
        data=contact_info.to_dict()
    )
    

@organization_router.delete("/contact-infos/{info_id}", status_code=200, response_model=success_response)
async def delete_organization_contact_info(
    info_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete an organization contact info"""
    
    # Get contact info
    contact_info = ContactInfo.fetch_by_id(db, info_id)
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=contact_info.model_id,
        permission='contact_info:delete',
        db=db
    )

    ContactInfo.soft_delete(db, contact_info.id)
    
    return success_response(
        message=f"Contact info deleted successfully",
        status_code=200
    )
    

@organization_router.post("{id}/locations", status_code=201, response_model=success_response)
async def create_organization_location(
    id: str,
    payload: location_schemas.LocationBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to add a new location to an organization"""
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=id,
        permission='location:create',
        db=db
    )

    payload.model_name = 'organizations'
    payload.model_id = id
    location = Location.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        message=f"New location created successfully",
        status_code=201,
        data=location.to_dict()
    )
    

@organization_router.get("{id}/locations", status_code=200, response_model=success_response)
async def get_organization_locations(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all organization locations"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=id,
        db=db
    )

    query, locations, count = Location.fetch_by_field(
        db=db,
        model_name='organizations',
        model_id=id
    )
        
    return success_response(
        message=f"Locations fetched successfully",
        status_code=201,
        data=[location.to_dict() for location in locations]
    )


@organization_router.patch("/locations/{location_id}", status_code=200, response_model=success_response)
async def update_organization_location(
    location_id: str,
    payload: location_schemas.UpdateLocation,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update an organization location"""
    
    # Get contact info
    location = Location.fetch_by_id(db, location_id)
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=location.model_id,
        permission='location:update',
        db=db
    )

    location = Location.update(
        db=db,
        id=location.id,
        **payload.model_dump(exclude_unset=True)
    )
    
    return success_response(
        message=f"Location updated successfully",
        status_code=200,
        data=location.to_dict()
    )
    

@organization_router.delete("/locations/{location_id}", status_code=200, response_model=success_response)
async def delete_organization_location(
    location_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete an organization location"""
    
    # Get contact info
    location = Location.fetch_by_id(db, location_id)
    
    AuthService.has_org_permission(
        entity=entity,
        organization_id=location.model_id,
        permission='location:delete',
        db=db
    )

    Location.soft_delete(db, location.id)
    
    return success_response(
        message=f"Location deleted successfully",
        status_code=200
    )
