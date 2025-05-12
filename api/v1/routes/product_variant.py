from fastapi import APIRouter, Depends
from slugify import slugify
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.user import User
from api.v1.models.product import ProductVariant
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.product import ProductService
from api.v1.schemas import product as product_schemas
from api.utils.loggers import create_logger


product_variant_router = APIRouter(prefix='/product-variants', tags=['Product Variant'])
logger = create_logger(__name__)

@product_variant_router.post("", status_code=201, response_model=success_response)
async def create_product_variant(
    payload: product_schemas.ProductVariantCreate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new product variant"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='product-variant:create',
        organization_id=payload.organization_id
    )
    
    if payload.attributes:
        payload.attributes = helpers.format_additional_info_create(payload.attributes)
    
    if not payload.slug:
        payload.slug = slugify(payload.name)
        
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )

    product_variant = ProductVariant.create(
        db=db,
        **payload.model_dump(exclude_unset=True)
    )

    return success_response(
        message=f"Product variant created successfully",
        status_code=201,
        data=product_variant.to_dict()
    )


@product_variant_router.get("", status_code=200)
async def get_product_variants(
    organization_id: str,
    name: str = None,
    slug: str = None,
    product_id: str = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all product variants"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, product_variants, count = ProductVariant.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
        },
        organization_id=organization_id,
        product_id=product_id,
        slug=slug
    )
    
    return paginator.build_paginated_response(
        items=[product_variant.to_dict() for product_variant in product_variants],
        endpoint='/product-variants',
        page=page,
        size=per_page,
        total=count,
    )


@product_variant_router.get("/{id}", status_code=200, response_model=success_response)
async def get_product_variant_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a product variant by ID or unique_id in case ID fails."""

    product_variant = ProductVariant.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=product_variant.organization_id,
        db=db
    )
    
    return success_response(
        message=f"Fetched product variant successfully",
        status_code=200,
        data=product_variant.to_dict()
    )


@product_variant_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_product_variant(
    id: str,
    organization_id: str,
    payload: product_schemas.ProductVariantUpdate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a product variant"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='product-variant:update',
        organization_id=organization_id
    )

    product_variant = ProductVariant.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=['attributes', 'attributes_keys_to_remove'])
    )
    
    if payload.attributes:
        product_variant.attributes = helpers.format_attributes_update(
            attributes=payload.attributes,
            model_instance=product_variant,
            keys_to_remove=payload.attributes_keys_to_remove
        )
        
    db.commit()

    logger.info(f'Variant with {product_variant.id} updated')
    
    return success_response(
        message=f"Product variant updated successfully",
        status_code=200,
        data=product_variant.to_dict()
    )


@product_variant_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_product_variant(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a product variant"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='product-variant:delete',
        organization_id=organization_id
    )

    ProductVariant.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200
    )

