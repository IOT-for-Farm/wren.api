from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.product import Product, ProductVariant
from api.v1.schemas import product as product_schemas


logger = create_logger(__name__)

class ProductService:
    
    @classmethod
    def product_belongs_to_organization(cls, db: Session, product_id: str, organization_id: str):
        '''Function to check if a product belongs to an organization'''
        
        product = Product.fetch_by_id(db, product_id)
        
        if product.organization_id != organization_id:
            raise HTTPException(403, 'Product does not belong in organization')
        
        return True
    
    @classmethod
    def product_variant_belongs_to_organization(cls, db: Session, varinat_id: str, organization_id: str):
        '''Function to check if a product variant belongs to an organization'''
        
        product_variant = ProductVariant.fetch_by_id(db, varinat_id)
        
        if product_variant.organization_id != organization_id:
            raise HTTPException(403, 'Product variant does not belong in organization')
        
        return True
