from typing import Dict, Any, List, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Session, class_mapper
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy.ext.hybrid import hybrid_property
from inspect import getmembers

from api.db.database import Base


class BaseTableModel(Base):
    """This model creates helper methods for all models"""

    __abstract__ = True

    # Add flag to skip logging dynamically
    _disable_activity_logging = False
    
    id = sa.Column(sa.String, primary_key=True, index=True, default=lambda: str(uuid4().hex))
    unique_id = sa.Column(sa.String, nullable=True)
    is_deleted = sa.Column(sa.Boolean, server_default='false')
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())

    
    def to_dict(self, excludes: List[str] = []) -> Dict[str, Any]:
        """Returns a dictionary representation of the instance"""
        
        obj_dict = self.__dict__.copy()
        
        del obj_dict["_sa_instance_state"]
        del obj_dict["is_deleted"]
        obj_dict["id"] = self.id
        
        if self.created_at:
            obj_dict["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            obj_dict["updated_at"] = self.updated_at.isoformat()
            
        # Get hybrid properties
        for name, attr in getmembers(self):
            if isinstance(attr, hybrid_property):
                obj_dict[name] = getattr(self, name)
                
        # Exclude specified fields
        for exclude in excludes:
            if exclude in list(obj_dict.keys()):
                # for exclude in excludes:
                obj_dict.pop(exclude, None)
            
        return obj_dict


    @classmethod
    def create(cls, db: Session, **kwargs):
        """Creates a new instance of the model"""
        
        obj = cls(**kwargs)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @classmethod
    def all(
        cls, 
        db: Session,
        page: int = 1, 
        per_page: int = 10, 
        sort_by: str = "created_at", 
        order: str = "desc",
        show_deleted: bool = False,
        search_fields: Optional[Dict[str, Any]] = None
    ):
        """Fetches all instances with pagination and sorting"""
        
        query = db.query(cls).filter_by(is_deleted=False) if not show_deleted else db.query(cls)

        # Handle sorting
        if order == "desc":
            query = query.order_by(sa.desc(getattr(cls, sort_by)))
        else:
            query = query.order_by(getattr(cls, sort_by))
        
        # Apply search filters
        if search_fields:
            filtered_fields = {field: value for field, value in search_fields.items() if value is not None}
            
            for field, value in filtered_fields.items():
                query = query.filter(getattr(cls, field).ilike(f"%{value}%"))
            
        count = query.count()

        # Handle pagination
        offset = (page - 1) * per_page
        return query, query.offset(offset).limit(per_page).all(), count
         
    
    @classmethod
    def fetch_by_id(cls, db: Session, id: str):
        """Fetches a single instance by ID. (ignores soft-deleted records).\n
        If checking by ID fails, it checks by unique id before then throwing an error if it fails.
        """
        
        obj = db.query(cls).filter_by(id=id, is_deleted=False).first()
        if obj is None:
            # Check with unique_id
            obj = db.query(cls).filter_by(unique_id=id, is_deleted=False).first()
            
            if obj is None:
                raise HTTPException(status_code=404, detail=f"Record not found in table `{cls.__tablename__}`")
            
        return obj
    

    @classmethod
    def fetch_one_by_field(cls, db: Session, throw_error: bool=True, **kwargs):
        """Fetches one unique record that match the given field(s)"""
        
        kwargs["is_deleted"] = False
        obj = db.query(cls).filter_by(**kwargs).first()
        if obj is None and throw_error:
            raise HTTPException(status_code=404, detail=f"Record not found in table `{cls.__tablename__}`")
        return obj
    
    
    @classmethod
    def fetch_by_field(
        cls, 
        db: Session,
        page: Optional[int] = 1, 
        per_page: Optional[int] = 10,  
        order: str='desc', 
        sort_by: str = "created_at",
        show_deleted: bool = False,
        search_fields: Optional[Dict[str, Any]] = None,
        ignore_none_kwarg: bool = True,
        paginate: bool = True,
        **kwargs
    ):
        """Fetches all records that match the given field(s)"""
        
        query = db.query(cls)
    
        # Handle is_deleted logic
        if not show_deleted and hasattr(cls, "is_deleted"):
            query = query.filter(cls.is_deleted == False)
        
        # Dynamic kwargs filters (exact match)
        if kwargs:
            for field, value in kwargs.items():
                if ignore_none_kwarg and value is None:
                    continue
                
                if hasattr(cls, field):
                    query = query.filter(getattr(cls, field) == value)
        
        #  Sorting
        if order == "desc":
            query = query.order_by(sa.desc(getattr(cls, sort_by)))
        else:
            query = query.order_by(getattr(cls, sort_by))
            
        # Apply search filters
        if search_fields:
            filtered_fields = {field: value for field, value in search_fields.items() if value is not None}
            
            for field, value in filtered_fields.items():
                query = query.filter(getattr(cls, field).ilike(f"%{value}%"))
            
        count = query.count()
            
        # Handle pagination
        offset = (page - 1) * per_page
        if not paginate:
            return query, query.all(), count
        else:
            return query, query.offset(offset).limit(per_page).all(), count
        

    @classmethod
    def update(cls, db: Session, id: str, **kwargs):
        """Updates an instance with the given ID"""
        
        obj = db.query(cls).filter_by(id=id, is_deleted=False).first()
        if obj is None:
            raise HTTPException(status_code=404, detail=f"Record not found in table `{cls.__tablename__}`")
        for key, value in kwargs.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj
    

    @classmethod
    def soft_delete(cls, db: Session, id: str):
        """Performs a soft delete by setting is_deleted to True"""
        
        obj = db.query(cls).filter_by(id=id, is_deleted=False).first()
        if obj is None:
            raise HTTPException(status_code=404, detail=f"Record not found in table `{cls.__tablename__}`")
        
        obj.is_deleted = True
        db.commit()
        

    @classmethod
    def hard_delete(cls, db: Session, id: str):
        """Permanently deletes an instance by ID or unique_id in case ID fails."""
        
        obj = db.query(cls).filter_by(id=id).first()
        if obj is None:
            raise HTTPException(status_code=404, detail=f"Record not found in table `{cls.__tablename__}`")
        
        db.delete(obj)
        db.commit()

    
    @classmethod
    def search(
        cls, 
        db: Session,
        search_fields: Dict[str, str] = None, 
        page: int = 1, 
        per_page: int = 10,
        sort_by: str = "created_at", 
        order: str = "desc", 
        filters: Dict[str, Any] = None, 
        ignore_none_filter: bool = True
    ):
        """
        Performs a search on the model based on the provided fields and values.

        :param search_fields: A dictionary where keys are field names and values are search terms.
        :param page: The page number for pagination (default is 1).
        :param per_page: The number of records per page (default is 10).
        :return: A list of matching records.
        """
        
        # Start building the query
        query = db.query(cls)
        
        if filters:
            for field, value in filters.items():
                if ignore_none_filter and value is None:
                    continue
                
                query = query.filter(getattr(cls, field) == value)

        # Apply search filters
        if search_fields:
            filtered_fields = {field: value for field, value in search_fields.items() if value is not None}
            
            for field, value in filtered_fields.items():
                query = query.filter(getattr(cls, field).ilike(f"%{value}%"))

        # Exclude soft-deleted records
        query = query.filter(cls.is_deleted == False)
        
        # Sorting
        if order == "desc":
            query = query.order_by(sa.desc(getattr(cls, sort_by)))
        else:
            query = query.order_by(getattr(cls, sort_by))
            
        count = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        return query, query.offset(offset).limit(per_page).all(), count
