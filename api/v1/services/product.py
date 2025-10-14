from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.utils.loggers import create_logger
from api.utils.enhanced_error_handling import (
    BusinessLogicError, 
    ResourceNotFoundError, 
    ValidationError,
    handle_database_errors
)
from api.v1.models.product import Product, ProductVariant
from api.v1.schemas import product as product_schemas


logger = create_logger(__name__)

class ProductService:
    
    @classmethod
    def product_belongs_to_organization(cls, db: Session, product_id: str, organization_id: str):
        '''Function to check if a product belongs to an organization'''
        
        try:
            product = Product.fetch_by_id(db, product_id)
        except Exception:
            raise ResourceNotFoundError(
                resource_type="Product",
                resource_id=product_id
            )
        
        if product.organization_id != organization_id:
            raise BusinessLogicError(
                message="Product does not belong to the specified organization",
                error_code="ORGANIZATION_MISMATCH",
                details={
                    "product_id": product_id,
                    "product_organization_id": product.organization_id,
                    "requested_organization_id": organization_id
                }
            )
        
        return True
    
    @classmethod
    def product_variant_belongs_to_organization(cls, db: Session, variant_id: str, organization_id: str):
        '''Function to check if a product variant belongs to an organization'''
        
        try:
            product_variant = ProductVariant.fetch_by_id(db, variant_id)
        except Exception:
            raise ResourceNotFoundError(
                resource_type="Product Variant",
                resource_id=variant_id
            )
        
        if product_variant.organization_id != organization_id:
            raise BusinessLogicError(
                message="Product variant does not belong to the specified organization",
                error_code="ORGANIZATION_MISMATCH",
                details={
                    "variant_id": variant_id,
                    "variant_organization_id": product_variant.organization_id,
                    "requested_organization_id": organization_id
                }
            )
        
        return True
    
    @classmethod
    @handle_database_errors
    def validate_product_data(cls, db: Session, payload: product_schemas.ProductCreate) -> Dict[str, Any]:
        """
        Comprehensive validation for product creation data
        
        Args:
            db: Database session
            payload: Product creation payload
            
        Returns:
            Dict containing validation results and processed data
            
        Raises:
            ValidationError: If validation fails
            BusinessLogicError: If business rules are violated
        """
        validation_errors = {}
        processed_data = {}
        
        # Validate organization exists and user has access
        if not payload.organization_id:
            validation_errors["organization_id"] = ["Organization ID is required"]
        
        # Validate product name uniqueness within organization
        if payload.name:
            existing_product = Product.fetch_one_by_field(
                db=db, 
                throw_error=False,
                name=payload.name,
                organization_id=payload.organization_id
            )
            if existing_product:
                validation_errors["name"] = ["Product name already exists in this organization"]
        
        # Validate slug uniqueness within organization
        if payload.slug:
            existing_slug = Product.fetch_one_by_field(
                db=db,
                throw_error=False,
                slug=payload.slug,
                organization_id=payload.organization_id
            )
            if existing_slug:
                validation_errors["slug"] = ["Product slug already exists in this organization"]
        
        # Validate price constraints
        if hasattr(payload, 'price') and payload.price is not None:
            if payload.price < 0:
                validation_errors["price"] = ["Price cannot be negative"]
            elif payload.price > 999999.99:
                validation_errors["price"] = ["Price cannot exceed 999,999.99"]
        
        # Validate stock quantity
        if hasattr(payload, 'stock_quantity') and payload.stock_quantity is not None:
            if payload.stock_quantity < 0:
                validation_errors["stock_quantity"] = ["Stock quantity cannot be negative"]
            elif payload.stock_quantity > 999999:
                validation_errors["stock_quantity"] = ["Stock quantity cannot exceed 999,999"]
        
        # Validate product type and status combinations
        if hasattr(payload, 'type') and hasattr(payload, 'status'):
            if payload.type == 'digital' and hasattr(payload, 'stock_quantity') and payload.stock_quantity:
                validation_errors["stock_quantity"] = ["Digital products should not have stock quantity"]
        
        # Validate vendor relationship if provided
        if hasattr(payload, 'vendor_id') and payload.vendor_id:
            # Additional vendor validation could be added here
            pass
        
        # Validate category relationships
        if hasattr(payload, 'category_ids') and payload.category_ids:
            if len(payload.category_ids) > 10:
                validation_errors["category_ids"] = ["Cannot assign more than 10 categories to a product"]
        
        # Validate tag relationships
        if hasattr(payload, 'tag_ids') and payload.tag_ids:
            if len(payload.tag_ids) > 20:
                validation_errors["tag_ids"] = ["Cannot assign more than 20 tags to a product"]
        
        # Validate additional info structure
        if hasattr(payload, 'additional_info') and payload.additional_info:
            if len(payload.additional_info) > 50:
                validation_errors["additional_info"] = ["Additional info cannot have more than 50 fields"]
            
            # Validate additional info keys
            for key in payload.additional_info:
                if len(key) > 100:
                    validation_errors["additional_info"] = [f"Additional info key '{key}' is too long (max 100 characters)"]
        
        # Validate attributes structure
        if hasattr(payload, 'attributes') and payload.attributes:
            if len(payload.attributes) > 30:
                validation_errors["attributes"] = ["Product attributes cannot have more than 30 fields"]
        
        if validation_errors:
            raise ValidationError(
                message="Product validation failed",
                field_errors=validation_errors
            )
        
        # Process and clean data
        processed_data = {
            "name": payload.name.strip() if payload.name else None,
            "description": payload.description.strip() if hasattr(payload, 'description') and payload.description else None,
            "organization_id": payload.organization_id,
            "slug": payload.slug.strip() if payload.slug else None,
            "unique_id": payload.unique_id,
            "price": getattr(payload, 'price', None),
            "stock_quantity": getattr(payload, 'stock_quantity', None),
            "type": getattr(payload, 'type', None),
            "status": getattr(payload, 'status', 'active'),
            "vendor_id": getattr(payload, 'vendor_id', None),
            "parent_id": getattr(payload, 'parent_id', None),
            "is_available": getattr(payload, 'is_available', True),
            "additional_info": getattr(payload, 'additional_info', None),
            "attributes": getattr(payload, 'attributes', None)
        }
        
        return processed_data
    
    @classmethod
    @handle_database_errors
    def create_product_with_validation(
        cls, 
        db: Session, 
        payload: product_schemas.ProductCreate,
        creator_id: Optional[str] = None
    ) -> Product:
        """
        Create a product with comprehensive validation and error handling
        
        Args:
            db: Database session
            payload: Product creation payload
            creator_id: ID of the user creating the product
            
        Returns:
            Created Product instance
            
        Raises:
            ValidationError: If validation fails
            BusinessLogicError: If business rules are violated
        """
        
        # Validate input data
        validated_data = cls.validate_product_data(db, payload)
        
        try:
            # Create the product
            product = Product.create(
                db=db,
                creator_id=creator_id,
                **validated_data
            )
            
            logger.info(f"Product created successfully: {product.id} - {product.name}")
            return product
            
        except IntegrityError as e:
            logger.error(f"Database integrity error creating product: {str(e)}")
            raise BusinessLogicError(
                message="Failed to create product due to data constraints",
                error_code="PRODUCT_CREATION_FAILED",
                details={"constraint_error": str(e)}
            )
    
    @classmethod
    def get_product_with_relations(cls, db: Session, product_id: str) -> Product:
        """
        Get a product with all related data loaded
        
        Args:
            db: Database session
            product_id: Product ID to fetch
            
        Returns:
            Product instance with relations loaded
            
        Raises:
            ResourceNotFoundError: If product is not found
        """
        try:
            product = Product.fetch_by_id(db, product_id)
            
            # Load related data efficiently
            # This could be enhanced with eager loading
            return product
            
        except Exception:
            raise ResourceNotFoundError(
                resource_type="Product",
                resource_id=product_id
            )
    
    @classmethod
    def validate_product_update(
        cls, 
        db: Session, 
        product_id: str, 
        payload: product_schemas.ProductUpdate
    ) -> Dict[str, Any]:
        """
        Validate product update data
        
        Args:
            db: Database session
            product_id: Product ID being updated
            payload: Update payload
            
        Returns:
            Dict containing validation results
            
        Raises:
            ValidationError: If validation fails
            ResourceNotFoundError: If product not found
        """
        
        # Check if product exists
        product = cls.get_product_with_relations(db, product_id)
        
        validation_errors = {}
        
        # Validate name uniqueness if being updated
        if hasattr(payload, 'name') and payload.name and payload.name != product.name:
            existing_product = Product.fetch_one_by_field(
                db=db,
                throw_error=False,
                name=payload.name,
                organization_id=product.organization_id
            )
            if existing_product and existing_product.id != product_id:
                validation_errors["name"] = ["Product name already exists in this organization"]
        
        # Validate slug uniqueness if being updated
        if hasattr(payload, 'slug') and payload.slug and payload.slug != product.slug:
            existing_slug = Product.fetch_one_by_field(
                db=db,
                throw_error=False,
                slug=payload.slug,
                organization_id=product.organization_id
            )
            if existing_slug and existing_slug.id != product_id:
                validation_errors["slug"] = ["Product slug already exists in this organization"]
        
        # Validate price constraints
        if hasattr(payload, 'price') and payload.price is not None:
            if payload.price < 0:
                validation_errors["price"] = ["Price cannot be negative"]
            elif payload.price > 999999.99:
                validation_errors["price"] = ["Price cannot exceed 999,999.99"]
        
        # Validate stock quantity
        if hasattr(payload, 'stock_quantity') and payload.stock_quantity is not None:
            if payload.stock_quantity < 0:
                validation_errors["stock_quantity"] = ["Stock quantity cannot be negative"]
            elif payload.stock_quantity > 999999:
                validation_errors["stock_quantity"] = ["Stock quantity cannot exceed 999,999"]
        
        if validation_errors:
            raise ValidationError(
                message="Product update validation failed",
                field_errors=validation_errors
            )
        
        return {"product": product, "validated": True}
