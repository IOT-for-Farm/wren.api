from typing import List
from slugify import slugify
from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.category import Category, CategoryAssociation
from api.v1.schemas import category as category_schemas


logger = create_logger(__name__)

class CategoryService:
    
    @classmethod
    def create_category_association(
        cls, 
        db: Session,
        category_ids: List[str],
        organization_id: str,
        model_type: str,
        entity_id: str
    ):
        '''Function to create a category association for an entity'''
        
        for category_id in category_ids:
            # Check that categorys exist in the organization
            category = Category.fetch_one_by_field(
                db, 
                throw_error=False,
                id=category_id, 
                organization_id=organization_id,
                model_type=model_type
            )
            
            # If category does not exist, skip
            if not category:
                # Assuming the category id is the name provided
                category = Category.create(
                    db=db,
                    name=category_id.lower(),
                    model_type=model_type,
                    organization_id=organization_id,
                    slug=slugify(category_id)
                )
            
            category_association = CategoryAssociation.fetch_one_by_field(
                db,
                throw_error=False,
                entity_id=entity_id,
                model_type=model_type,
                category_id=category.id,
            )
            
            # If category association exists, skip
            if category_association:
                continue
            
            # Create template category association
            CategoryAssociation.create(
                db=db,
                entity_id=entity_id,
                category_id=category.id,
                model_type=model_type
            )
            
    
    @classmethod
    def delete_category_association(
        cls, 
        db: Session,
        category_ids: List[str],
        organization_id: str,
        model_type: str,
        entity_id: str
    ):
        '''Function to delete a category association for an entity'''
        
        for category_id in category_ids:
            # Check that categorys exist in the organization
            category = Category.fetch_one_by_field(
                db, 
                throw_error=False,
                id=category_id, 
                organization_id=organization_id,
                model_type=model_type
            )
            
            # If category does not exist, skip
            if not category:
                continue
            
            category_association = CategoryAssociation.fetch_one_by_field(
                db,
                throw_error=False,
                entity_id=entity_id,
                model_type=model_type,
                category_id=category_id,
            )
            
            # If category association exists, skip
            if not category_association:
                continue
            
            # Delete category association
            CategoryAssociation.soft_delete(db, category_association.id)
