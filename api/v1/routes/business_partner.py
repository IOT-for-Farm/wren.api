from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from slugify import slugify
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.contact_info import ContactInfo
from api.v1.models.location import Location
from api.v1.models.user import User
from api.v1.models.business_partner import BusinessPartner
from api.v1.schemas.contact_info import ContactType
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.business_partner import BusinessPartnerService
from api.v1.schemas import business_partner as business_partner_schemas
from api.utils.loggers import create_logger


business_partner_router = APIRouter(prefix='/business-partners', tags=['Business Partner'])
logger = create_logger(__name__)

@business_partner_router.post("", status_code=201, response_model=success_response)
async def create_business_partner(
    payload: business_partner_schemas.BusinessPartnerBase,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new business partner"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='business-partner:create',
        organization_id=payload.organization_id
    )
    
    # Check if email already exists in the organization
    existing_email_in_org = BusinessPartner.fetch_one_by_field(
        db=db, throw_error=False,
        email=payload.email,
        organization_id=payload.organization_id
    )
    
    if existing_email_in_org:
        raise HTTPException(400, 'Email already exists for a business partner in organization')
    
    if payload.partner_type == 'vendor' and not payload.company_name:
        raise HTTPException(400, 'Vendors must have a company name')
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )
    
    if not payload.slug and payload.company_name:
        payload.slug = slugify(payload.company_name)
    
    if payload.additional_info:
        payload.additional_info = helpers.format_additional_info_create(payload.additional_info)
        
    if payload.password:
        payload.password = AuthService.hash_secret(payload.password)
    
    if not payload.image_url:
        payload.image_url = helpers.generate_logo_url(f"{payload.first_name} {payload.last_name}")

    business_partner = BusinessPartner.create(
        db=db,
        user_id=entity.entity.id if entity.type=='user' else None,
        **payload.model_dump(
            exclude_unset=True, 
            exclude=['state', 'city', 'country', 'address', 'postal_code']
        )
    )
    
    # Create email contact info
    ContactInfo.create(
        db=db,
        model_name='business_partners',
        model_id=business_partner.id,
        contact_type=ContactType.EMAIL.value,
        contact_data=payload.email,
        is_primary=True
    )
    logger.info('Email contact info added for business_partner')
    
    # Create phone number contact info
    if payload.phone and payload.phone_country_code:
        ContactInfo.create(
            db=db,
            model_name='business_partners',
            model_id=business_partner.id,
            contact_type=ContactType.PHONE.value,
            contact_data=payload.phone,
            phone_country_code=payload.phone_country_code,
            is_primary=True
        )
        logger.info('Phone contact info added for business_partner')
    
    if payload.address:
        # Create business_partner location
        Location.create(
            db=db,
            model_name='business_partners',
            model_id=business_partner.id,
            **payload.model_dump(
                exclude_unset=True,
                include=['state', 'city', 'country', 'address', 'postal_code']
            )
        )
        logger.info('Location added for business_partner')

    logger.info(f'Business partner with id {business_partner.id} created')
    return success_response(
        message=f"BusinessPartner created successfully",
        status_code=201,
        data=business_partner.to_dict()
    )
    

@business_partner_router.post('/login', status_code=200, response_model=success_response)
async def business_partner_login(payload: business_partner_schemas.BusinessPartnerLogin, db: Session=Depends(get_db)):
    """Endpoint to log in a business partner. 
    The ID of the business partner can be the unique identifier of the logged in user instead of an access token"""
    
    business_partner, access_token, refresh_token = BusinessPartnerService.authenticate(
        db, 
        email=payload.email.lower().strip(), 
        password=payload.password,
        create_token=False
    )
    
    logger.info(f'Business partner with id {business_partner.id} logged in successfully')
    
    response = success_response(
        status_code=200,
        message='Logged in successfully',
        # data={
        #     'access_token': access_token,
        #     'refresh_token': refresh_token,
        #     'business_partner': business_partner.to_dict()
        # }
        data=business_partner.to_dict()
    )
    
    # Add refresh token to cookies
    # response.set_cookie(
    #     key="refresh_token",
    #     value=refresh_token,
    #     expires=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    #     httponly=True,
    #     secure=True,
    #     samesite="none",
    # )
    
    return response


@business_partner_router.post("/attach-user", status_code=200, response_model=success_response)
async def attach_user_to_business_partners(
    organization_id: str,
    payload: business_partner_schemas.AttachUserToBusinessPartners,
    use_current_user: bool = None,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint toattach a user to multiple business bartners."""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='business-partner:attach-to-user',
        organization_id=organization_id
    )
    
    if use_current_user:
        user: User = entity.entity
    else:
        if not payload.user_id:
            raise HTTPException(400, 'User id is required')
        
        user = User.fetch_by_id(db, payload.user_id)

    for id in payload.business_partner_ids:
        business_partner = BusinessPartner.fetch_by_id(db, id)
        business_partner.user_id = user.id
    
    db.commit()
    
    return success_response(
        message=f"Attached user to business partners successfully",
        status_code=200,
    )


@business_partner_router.get("", status_code=200)
async def get_business_partners(
    organization_id: str,
    unique_id: str = None,
    first_name: str = None,
    last_name: str = None,
    partner_type: str = None,
    slug: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all business partners"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, business_partners, count = BusinessPartner.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'first_name': first_name,
            'last_name': last_name,
            'unique_id': unique_id,
        },
        organization_id=organization_id,
        partner_type=partner_type,
        slug=slug,
    )
    
    return paginator.build_paginated_response(
        items=[business_partner.to_dict() for business_partner in business_partners],
        endpoint='/business-partners',
        page=page,
        size=per_page,
        total=count,
    )


@business_partner_router.get("/{id}", status_code=200, response_model=success_response)
async def get_business_partner_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a business partner by ID or unique_id in case ID fails."""

    business_partner = BusinessPartner.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=business_partner.organization_id,
        db=db
    )
    
    return success_response(
        message=f"Fetched business_partner successfully",
        status_code=200,
        data=business_partner.to_dict()
    )


@business_partner_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_business_partner(
    id: str,
    organization_id: str,
    payload: business_partner_schemas.UpdateBusinessPartner,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a business partner"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='business-partner:update',
        organization_id=organization_id
    )
    
    current_partner = BusinessPartner.fetch_by_id(db, id)
    
    if payload.email:
        # Check if email already exists in the organization
        existing_email_in_org = BusinessPartner.fetch_one_by_field(
            db=db, throw_error=False,
            email=payload.email,
            organization_id=organization_id
        )
        
        if existing_email_in_org and current_partner.id != id:
            raise HTTPException(400, 'Email already exists for a business partner in organization')
    
    if payload.password:
        payload.password = AuthService.hash_secret(payload.password)
        
    if not payload.image_url and (payload.first_name and payload.last_name):
        payload.image_url = helpers.generate_logo_url(f"{payload.first_name} {payload.last_name}")
        
    if not payload.image_url and payload.first_name:
        payload.image_url = helpers.generate_logo_url(f"{payload.first_name} {current_partner.last_name}")
        
    if not payload.image_url and payload.last_name:
        payload.image_url = helpers.generate_logo_url(f"{current_partner.first_name} {payload.last_name}")

    business_partner = BusinessPartner.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['additional_info', 'additional_info_keys_to_remove'])
    )
    
    if payload.additional_info:
        business_partner.additional_info = helpers.format_additional_info_update(
            additional_info=payload.additional_info,
            model_instance=business_partner,
            keys_to_remove=payload.additional_info_keys_to_remove
        )
    
    db.commit()

    logger.info(f'Business partner with id {business_partner.id} updated')
    
    return success_response(
        message=f"BusinessPartner updated successfully",
        status_code=200,
        data=business_partner.to_dict()
    )


@business_partner_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_business_partner(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a business partner"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='business-partner:delete',
        organization_id=organization_id
    )

    BusinessPartner.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )
