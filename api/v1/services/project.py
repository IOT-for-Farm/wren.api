from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.loggers import create_logger
from api.v1.models.project import Project, ProjectMember
from api.v1.models.user import User
from api.v1.schemas import project as project_schemas
from api.v1.schemas.auth import AuthenticatedEntity, EntityType
from api.v1.services.auth import AuthService


logger = create_logger(__name__)

class ProjectService:
    
    @classmethod
    def check_project_role(
        cls, 
        project_id: str,
        entity: AuthenticatedEntity=Depends(AuthService.get_current_user_entity),
        roles: List[str] = ['*'],  # default to allow all roles
        db: Session = Depends(get_db)
    ):
        '''Function to check if an authenticated endtity has the permission to handle an action'''
        
        project = Project.fetch_by_id(db, project_id)
        
        # Get project members
        project_members = project.members
        project_member_user_ids = [member.id for member in project_members]
        
        if entity.type == EntityType.USER:
            user: User = entity.entity
        
            if user.is_superuser:
                return True
            
            if '*' in roles:
                return True
            
            # Check id entity belongs in project
            if user.id in project_member_user_ids:
                project_member = ProjectMember.fetch_one_by_field(
                    db=db, throw_error=False,
                    project_id=project_id,
                    user_id=user.id
                )
                
                # Get role of user in project
                role = project_member.role  # one of owner, admin, member, viewer
                
                if role in roles:
                    return True
        
        if entity.type == EntityType.APIKEY:
            return True
        
        logger.info(f'Entity ({entity.type.value}) with role `{role}` is not allowed')
        raise HTTPException(403, 'You do not have the permission to access this resource')    

