from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.business_partner import BusinessPartner
from api.v1.models.user import User
from api.v1.models.vendor import Vendor
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.category import CategoryService
from api.v1.services.tag import TagService
from api.v1.services.vendor import VendorService
from api.v1.schemas import vendor as vendor_schemas
from api.utils.loggers import create_logger


vendor_router = APIRouter(prefix='/vendors', tags=['Vendor'])
logger = create_logger(__name__)

@vendor_router.post("", status_code=201, response_model=success_response)
async def create_vendor(
    business_partner_id: str,
    organization_id: str,
    payload: vendor_schemas.VendorCreate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new vendor"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='vendor:create',
        organization_id=organization_id
    )
    
    # Check if business partner exists
    BusinessPartner.fetch_one_by_field(
        db=db,
        id=business_partner_id,
        partner_type="vendor"
    )
    
    # Check for existing vendor
    existing_vendor = Vendor.fetch_one_by_field(
        db=db, throw_error=False,
        business_partner_id=business_partner_id
    )
    
    if existing_vendor:
        raise HTTPException(400, "Vendor with this business partner id already exists")
    
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=organization_id,
        )

    vendor = Vendor.create(
        db=db,
        business_partner_id=business_partner_id,
        **payload.model_dump(exclude_unset=True, exclude=['tag_ids', 'category_ids'])
    )
    
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=organization_id,
            model_type='vendors',
            entity_id=vendor.id
        )
        
    if payload.category_ids:
        CategoryService.create_category_association(
            db=db,
            category_ids=payload.category_ids,
            organization_id=organization_id,
            model_type='vendors',
            entity_id=vendor.id
        )

    return success_response(
        message=f"Vendor created successfully",
        status_code=201,
        data=vendor.to_dict()
    )


@vendor_router.get("", status_code=200)
async def get_vendors(
    organization_id: str,
    vendor_type: str = None,
    payment_terms: str = None,
    first_name: str = None,
    last_name: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all vendors"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, vendors, count = Vendor.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={},
        payment_terms=payment_terms,
        vendor_type=vendor_type
    )
    
    query = (
        query
        .join(BusinessPartner, BusinessPartner.id==Vendor.business_partner_id)
        .filter(
            BusinessPartner.partner_type=='vendor',
            BusinessPartner.organization_id== organization_id
        )
    )
    
    if first_name:
        query = query.filter(BusinessPartner.first_name.ilike(f"%{first_name}%"))
        
    if last_name:
        query = query.filter(BusinessPartner.last_name.ilike(f"%{last_name}%"))
    
    vendors = query.all()
    count = query.count()
    
    return paginator.build_paginated_response(
        items=[vendor.to_dict() for vendor in vendors],
        endpoint='/vendors',
        page=page,
        size=per_page,
        total=count,
    )


@vendor_router.get("/{id}", status_code=200, response_model=success_response)
async def get_vendor_by_id(
    organization_id: str,
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a vendor by ID or unique_id in case ID fails."""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    vendor = Vendor.fetch_by_id(db, id)
    
    return success_response(
        message=f"Fetched vendor successfully",
        status_code=200,
        data=vendor.to_dict()
    )


@vendor_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_vendor(
    id: str,
    organization_id: str,
    payload: vendor_schemas.UpdateVendor,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a vendor"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='vendor:update',
        organization_id=organization_id
    )

    vendor = Vendor.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['tag_ids', 'category_ids'])
    )
    
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=organization_id,
            model_type='vendors',
            entity_id=vendor.id
        )
        
    if payload.category_ids:
        CategoryService.create_category_association(
            db=db,
            category_ids=payload.category_ids,
            organization_id=organization_id,
            model_type='vendors',
            entity_id=vendor.id
        )

    return success_response(
        message=f"Vendor updated successfully",
        status_code=200,
        data=vendor.to_dict()
    )


@vendor_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_vendor(
    organization_id: str,
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a vendor"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='vendor:delete',
        organization_id=organization_id
    )

    Vendor.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

