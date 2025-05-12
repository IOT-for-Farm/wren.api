import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.db.database import get_db, get_db_with_ctx_manager
from api.core.dependencies.permissions import ROLE_PERMISSIONS
from api.v1.models.organization import OrganizationRole, Organization

# db = next(get_db())

def seed_role_permissions():
    """Seed role permissions into the database."""
    
    with get_db_with_ctx_manager() as db:
        # with get_db() as db:
        for role_name, permissions in ROLE_PERMISSIONS.items():
            # Check if the role already exists
            existing_role = OrganizationRole.fetch_one_by_field(
                db=db,
                throw_error=False,
                role_name=role_name,
                is_deleted=False,
                organization_id='-1'
            )
            
            if not existing_role:
                # Create a new role with the specified permissions
                OrganizationRole.create(
                    db=db,
                    role_name=role_name,
                    permissions=permissions,
                    organization_id='-1'
                )
                
                print(f'New role: {role_name} created')
            
            else:
                # Update the role with the new permissions
                OrganizationRole.update(
                    db=db,
                    id=existing_role.id,
                    permissions=permissions
                )
                
                print(f'Role: {role_name} updated')
            
            
if __name__ == "__main__":
    seed_role_permissions()
