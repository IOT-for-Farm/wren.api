from fastapi import APIRouter, Depends
from slugify import slugify
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils import paginator, helpers
from api.utils.responses import success_response
from api.utils.settings import settings
from api.v1.models.tag import TagAssociation, Tag
from api.v1.models.user import User
from api.v1.models.product import Product
from api.v1.services.auth import AuthService
from api.v1.schemas.auth import AuthenticatedEntity
from api.v1.services.category import CategoryService
from api.v1.services.product import ProductService
from api.v1.schemas import product as product_schemas
from api.utils.loggers import create_logger
from api.v1.services.tag import TagService


product_router = APIRouter(prefix='/products', tags=['Product'])
logger = create_logger(__name__)

@product_router.post("", status_code=201, response_model=success_response)
async def create_product(
    payload: product_schemas.ProductCreate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to create a new product"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='product:create',
        organization_id=payload.organization_id
    )
    
    if not payload.slug:
        payload.slug = slugify(payload.name)
        
    if not payload.unique_id:
        payload.unique_id = helpers.generate_unique_id(
            db=db, 
            organization_id=payload.organization_id,
        )
    
    if payload.additional_info:
        payload.additional_info = helpers.format_additional_info_create(payload.additional_info)
        
    if payload.attributes:
        payload.attributes = helpers.format_additional_info_create(payload.attributes)

    product = Product.create(
        db=db,
        creator_id=entity.entity.id if entity.type == 'user' else None,
        **payload.model_dump(exclude_unset=True, exclude=['category_ids', 'tag_ids'])
    )
    
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=payload.organization_id,
            model_type='products',
            entity_id=product.id
        )
        
    if payload.category_ids:
        CategoryService.create_category_association(
            db=db,
            category_ids=payload.category_ids,
            organization_id=payload.organization_id,
            model_type='products',
            entity_id=product.id
        )

    logger.info(f'Product with {product.id} created')
    
    return success_response(
        message=f"Product created successfully",
        status_code=200,
        data=product.to_dict()
    )


@product_router.get("", status_code=200)
async def get_products(
    organization_id: str,
    unique_id: str = None,
    name: str = None,
    slug: str = None,
    status: str = None,
    type: str = None,
    vendor_id: str = None,
    parent_id: str = None,
    get_parents: bool = None,
    tags: str = None,
    is_available: bool = None,
    page: int = 1,
    per_page: int = 10,
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get all products"""
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=organization_id,
        db=db
    )

    query, products, count = Product.fetch_by_field(
        db, 
        sort_by=sort_by,
        order=order.lower(),
        page=page,
        per_page=per_page,
        search_fields={
            'name': name,
            'unique_id': unique_id,
        },
        organization_id=organization_id,
        slug=slug,
        status=status,
        type=type,
        is_available=is_available,
        vendor_id=vendor_id,
        parent_id=parent_id,
    )
    
    if tags:
        tags_list = [tag.strip() for tag in tags.split(',')]      
        query = (
            query
            .join(TagAssociation, TagAssociation.entity_id==Product.id)
            .join(Tag, Tag.id == TagAssociation.tag_id)
            .filter(Tag.name.in_(tags_list))
        )
    
    if get_parents == True:
        query = query.filter(Product.parent_id == None)
        
    if get_parents == False:
        query = query.filter(Product.parent_id != None)
        
    products, count = paginator.paginate_query(query, page, per_page)
    
    return paginator.build_paginated_response(
        items=[product.to_dict() for product in products],
        endpoint='/products',
        page=page,
        size=per_page,
        total=count,
    )


@product_router.get("/{id}", status_code=200, response_model=success_response)
async def get_product_by_id(
    id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to get a product by ID or unique_id in case ID fails."""

    product = Product.fetch_by_id(db, id)
    
    AuthService.belongs_to_organization(
        entity=entity,
        organization_id=product.organization_id,
        db=db
    )
    
    return success_response(
        message=f"Fetched product successfully",
        status_code=200,
        data=product.to_dict()
    )


@product_router.patch("/{id}", status_code=200, response_model=success_response)
async def update_product(
    id: str,
    organization_id: str,
    payload: product_schemas.ProductUpdate,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to update a product"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='product:update',
        organization_id=organization_id
    )
    
    if payload.status:
        payload.status = payload.status.value
    
    if payload.type:
        payload.type = payload.type.value

    product = Product.update(
        db=db,
        id=id,
        **payload.model_dump(exclude_unset=True, exclude=[
            'category_ids', 'tag_ids', 
            'additional_info', 'attributes',
            'additional_info_keys_to_remove', 'attributes_keys_to_remove'
        ])
    )
    
    if payload.additional_info:
        product.additional_info = helpers.format_additional_info_update(
            additional_info=payload.additional_info,
            model_instance=product,
            keys_to_remove=payload.additional_info_keys_to_remove
        )
        
    if payload.attributes:
        product.attributes = helpers.format_attributes_update(
            attributes=payload.attributes,
            model_instance=product,
            keys_to_remove=payload.attributes_keys_to_remove
        )
        
    db.commit()
    
    if payload.tag_ids:
        TagService.create_tag_association(
            db=db,
            tag_ids=payload.tag_ids,
            organization_id=organization_id,
            model_type='products',
            entity_id=product.id
        )
        
    if payload.category_ids:
        CategoryService.create_category_association(
            db=db,
            category_ids=payload.category_ids,
            organization_id=organization_id,
            model_type='products',
            entity_id=product.id
        )

    logger.info(f'Product with {product.id} updated')
    
    return success_response(
        message=f"Product updated successfully",
        status_code=200,
        data=product.to_dict()
    )


@product_router.delete("/{id}", status_code=200, response_model=success_response)
async def delete_product(
    id: str,
    organization_id: str,
    db: Session=Depends(get_db), 
    entity: AuthenticatedEntity=Depends(AuthService.get_current_entity)
):
    """Endpoint to delete a product"""
    
    AuthService.has_org_permission(
        db=db, entity=entity,
        permission='product:delete',
        organization_id=organization_id
    )

    Product.soft_delete(db, id)

    return success_response(
        message=f"Deleted successfully",
        status_code=200,
    )

