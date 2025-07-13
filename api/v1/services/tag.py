from typing import List
from slugify import slugify
from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.tag import Tag, TagAssociation
from api.v1.schemas import tag as tag_schemas


logger = create_logger(__name__)

class TagService:
    
    @classmethod
    def create_tag_association(
        cls, 
        db: Session,
        tag_ids: List[str],
        organization_id: str,
        model_type: str,
        entity_id: str
    ):
        '''Function to create a tag association for an entity'''
        
        for tag_id in tag_ids:
            # Check that tags exist in the organization
            tag = Tag.fetch_one_by_field(
                db, 
                throw_error=False,
                id=tag_id, 
                organization_id=organization_id,
                model_type=model_type
            )
            
            # If tag does not exist, skip
            if not tag:
                # Assuming the tag id is the name provided
                tag = Tag.create(
                    db=db,
                    name=tag_id.lower(),
                    model_type=model_type,
                    organization_id=organization_id,
                )
            
            tag_association = TagAssociation.fetch_one_by_field(
                db,
                throw_error=False,
                entity_id=entity_id,
                model_type=model_type,
                tag_id=tag.id,
            )
            
            # If tag association exists, skip
            if tag_association:
                continue
            
            # Create template tag association
            TagAssociation.create(
                db=db,
                entity_id=entity_id,
                tag_id=tag.id,
                model_type=model_type
            )

    
    @classmethod
    def delete_tag_association(
        cls, 
        db: Session,
        tag_ids: List[str],
        organization_id: str,
        model_type: str,
        entity_id: str
    ):
        '''Function to delete a tag association for an entity'''
        
        for tag_id in tag_ids:
            # Check that tags exist in the organization
            tag = Tag.fetch_one_by_field(
                db, 
                throw_error=False,
                id=tag_id, 
                organization_id=organization_id,
                model_type=model_type
            )
            
            # If tag does not exist, skip
            if not tag:
                continue
            
            tag_association = TagAssociation.fetch_one_by_field(
                db,
                throw_error=False,
                entity_id=entity_id,
                model_type=model_type,
                tag_id=tag_id,
            )
            
            # If tag association exists, skip
            if not tag_association:
                continue
            
            # Delete tag association
            TagAssociation.soft_delete(db, tag_association.id)
