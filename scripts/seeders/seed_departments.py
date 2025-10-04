import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.department import Department, DepartmentMember, DepartmentRole
from api.v1.models.organization import Organization
from api.v1.models.user import User
from api.db.database import get_db_with_ctx_manager


def seed_departments():
    '''Seed departments, department roles, and department members'''
    
    with get_db_with_ctx_manager() as db:
        # Get required dependencies
        greentrac_org = Organization.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug="greentrac-tech"
        )
        
        ecofriendly_org = Organization.fetch_one_by_field(
            db=db,
            throw_error=False,
            slug="ecofriendly-solutions"
        )
        
        users = User.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        if not greentrac_org or not users:
            print("Required dependencies not found. Please run seed_organizations.py and seed_users.py first.")
            return
        
        # Create departments for GreenTrac
        greentrac_departments = [
            {
                "organization_id": greentrac_org.id,
                "creator_id": users[0].id,
                "name": "Engineering",
                "parent_id": None,
                "additional_info": {
                    "description": "Technical development and engineering solutions",
                    "location": "Lagos Office",
                    "head_count": 8,
                    "specialties": ["Solar Systems", "Wind Energy", "Battery Storage"]
                },
                "is_active": True
            },
            {
                "organization_id": greentrac_org.id,
                "creator_id": users[0].id,
                "name": "Sales & Marketing",
                "parent_id": None,
                "additional_info": {
                    "description": "Sales, marketing, and customer acquisition",
                    "location": "Lagos Office",
                    "head_count": 6,
                    "target_markets": ["Residential", "Commercial", "Industrial"]
                },
                "is_active": True
            },
            {
                "organization_id": greentrac_org.id,
                "creator_id": users[1].id,
                "name": "Customer Success",
                "parent_id": None,
                "additional_info": {
                    "description": "Customer support and success management",
                    "location": "Abuja Office",
                    "head_count": 4,
                    "services": ["Installation Support", "Maintenance", "Training"]
                },
                "is_active": True
            },
            {
                "organization_id": greentrac_org.id,
                "creator_id": users[0].id,
                "name": "Solar Installation",
                "parent_id": None,  # Will be set after parent department is created
                "additional_info": {
                    "description": "Specialized solar panel installation services",
                    "location": "Lagos Office",
                    "head_count": 5,
                    "certifications": ["NABCEP", "OSHA"]
                },
                "is_active": True
            },
            {
                "organization_id": greentrac_org.id,
                "creator_id": users[1].id,
                "name": "Project Management",
                "parent_id": None,
                "additional_info": {
                    "description": "Project planning and execution oversight",
                    "location": "Lagos Office",
                    "head_count": 3,
                    "methodology": "Agile PM",
                    "tools": ["Microsoft Project", "Jira", "Trello"]
                },
                "is_active": True
            }
        ]
        
        # Create departments for EcoFriendly
        ecofriendly_departments = [
            {
                "organization_id": ecofriendly_org.id if ecofriendly_org else greentrac_org.id,
                "creator_id": users[2].id if len(users) > 2 else users[0].id,
                "name": "Environmental Consulting",
                "parent_id": None,
                "additional_info": {
                    "description": "Environmental impact assessments and consulting",
                    "location": "Abuja Office",
                    "head_count": 4,
                    "specialties": ["EIA", "Environmental Compliance", "Sustainability"]
                },
                "is_active": True
            },
            {
                "organization_id": ecofriendly_org.id if ecofriendly_org else greentrac_org.id,
                "creator_id": users[2].id if len(users) > 2 else users[0].id,
                "name": "Research & Development",
                "parent_id": None,
                "additional_info": {
                    "description": "Research and development of sustainable solutions",
                    "location": "Abuja Office",
                    "head_count": 3,
                    "focus_areas": ["Renewable Energy", "Waste Management", "Green Technology"]
                },
                "is_active": True
            }
        ]
        
        all_departments = greentrac_departments + ecofriendly_departments
        created_departments = []
        
        # Create departments
        for dept_data in all_departments:
            existing_dept = Department.fetch_one_by_field(
                db=db,
                throw_error=False,
                name=dept_data['name'],
                organization_id=dept_data['organization_id']
            )
            
            if not existing_dept:
                new_dept = Department.create(
                    db=db,
                    **dept_data
                )
                created_departments.append(new_dept)
                print(f"Department '{new_dept.name}' created for {new_dept.organization.name}")
                
                # Create department roles
                roles_data = [
                    {
                        "department_id": new_dept.id,
                        "role_name": "Manager",
                        "description": f"Department manager for {new_dept.name}",
                        "permissions": ["read", "write", "delete", "manage_users", "approve_budget"]
                    },
                    {
                        "department_id": new_dept.id,
                        "role_name": "Senior Specialist",
                        "description": f"Senior specialist role in {new_dept.name}",
                        "permissions": ["read", "write", "mentor_junior"]
                    },
                    {
                        "department_id": new_dept.id,
                        "role_name": "Specialist",
                        "description": f"Specialist role in {new_dept.name}",
                        "permissions": ["read", "write"]
                    },
                    {
                        "department_id": new_dept.id,
                        "role_name": "Junior",
                        "description": f"Junior role in {new_dept.name}",
                        "permissions": ["read"]
                    }
                ]
                
                created_roles = []
                for role_data in roles_data:
                    existing_role = DepartmentRole.fetch_one_by_field(
                        db=db,
                        throw_error=False,
                        department_id=new_dept.id,
                        role_name=role_data['role_name']
                    )
                    
                    if not existing_role:
                        new_role = DepartmentRole.create(
                            db=db,
                            **role_data
                        )
                        created_roles.append(new_role)
                        print(f"  - Role created: {new_role.role_name}")
                
                # Create department members
                num_members = min(3, len(users))
                selected_users = users[:num_members]
                
                for i, user in enumerate(selected_users):
                    role = created_roles[0] if i == 0 else created_roles[1] if i == 1 else created_roles[2] if len(created_roles) > 2 else created_roles[0]
                    
                    member_data = {
                        "user_id": user.id,
                        "department_id": new_dept.id,
                        "role_id": role.id,
                        "is_primary": i == 0,  # First user is primary
                        "join_date": None  # Will use default
                    }
                    
                    new_member = DepartmentMember.create(
                        db=db,
                        **member_data
                    )
                    print(f"  - Member added: {user.first_name} {user.last_name} ({role.role_name})")
            else:
                print(f"Department '{existing_dept.name}' already exists")
        
        # Set parent-child relationships for departments
        if created_departments:
            # Make Solar Installation a child of Engineering
            engineering_dept = None
            solar_dept = None
            
            for dept in created_departments:
                if dept.name == "Engineering":
                    engineering_dept = dept
                elif dept.name == "Solar Installation":
                    solar_dept = dept
            
            if engineering_dept and solar_dept:
                solar_dept.parent_id = engineering_dept.id
                db.commit()
                print(f"Set {solar_dept.name} as child of {engineering_dept.name}")
        
        print(f"Total departments created: {len(created_departments)}")


if __name__ == "__main__":
    seed_departments()
