from typing import List
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
        '''Function to ceate a tag association for an entity'''
        
        for category_id in category_ids:
            # Check that tags exist in the organization
            tag = Category.fetch_one_by_field(
                db, 
                throw_error=False,
                id=category_id, 
                organization_id=organization_id,
                model_type=model_type
            )
            
            # If tag does not exist, skip
            if not tag:
                continue
            
            category_association = CategoryAssociation.fetch_one_by_field(
                db,
                throw_error=False,
                entity_id=entity_id,
                model_type=model_type,
                category_id=category_id,
            )
            
            # If tag association exists, skip
            if category_association:
                continue
            
            # Create template tag association
            CategoryAssociation.create(
                db=db,
                entity_id=entity_id,
                category_id=category_id,
                model_type=model_type
            )

