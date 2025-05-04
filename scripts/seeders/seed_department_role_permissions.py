import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.db.database import get_db
from api.core.dependencies.permissions import DEFAULT_DEPARTMENT_ROLES
from api.v1.models.department import DepartmentRole


db = next(get_db())

def seed_department_roles():
    """Seed default department roles into the database."""
    
    for role in DEFAULT_DEPARTMENT_ROLES:
        # Check if role exists
        existing_role = DepartmentRole.fetch_one_by_field(
            db=db, throw_error=False,
            role_name=role['name'],
            is_deleted=False,
            department_id='-1'
        )
        
        if not existing_role:
            # Create a new role with the specified permissions
            DepartmentRole.create(
                db=db,
                role_name=role['name'],
                description=role['description'],
                permissions=role['permissions'],
                department_id='-1',
            )
            
            print(f'New role: {role["name"]} created')
        
        else:
            # Update the role with the new permissions
            DepartmentRole.update(
                db=db,
                id=existing_role.id,
                permissions=role['permissions']
            )
            
            print(f'Role: {role["name"]} updated')
            
            
if __name__ == "__main__":
    seed_department_roles()
