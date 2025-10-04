import sys
import pathlib
from datetime import datetime, timedelta

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.project import Project, ProjectMember, Milestone
from api.v1.models.organization import Organization
from api.v1.models.department import Department
from api.v1.models.user import User
from api.db.database import get_db_with_ctx_manager


def seed_projects():
    """Seed projects and project members"""
    
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
        
        departments = Department.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        if not greentrac_org or not users:
            print("Required dependencies not found. Please run seed_organizations.py and seed_users.py first.")
            return
        
        # Get specific departments
        engineering_dept = None
        sales_dept = None
        customer_dept = None
        installation_dept = None
        project_dept = None
        environmental_dept = None
        rnd_dept = None
        
        for dept in departments:
            if "Engineering" in dept.name:
                engineering_dept = dept
            elif "Sales" in dept.name:
                sales_dept = dept
            elif "Customer" in dept.name:
                customer_dept = dept
            elif "Installation" in dept.name:
                installation_dept = dept
            elif "Project" in dept.name:
                project_dept = dept
            elif "Environmental" in dept.name:
                environmental_dept = dept
            elif "Research" in dept.name:
                rnd_dept = dept
        
        # Create projects for GreenTrac
        greentrac_projects = [
            {
                "name": "Solar Installation Project - Lagos Residential",
                "description": "Complete solar panel installation for residential properties in Lagos, including system design, procurement, installation, and commissioning.",
                "organization_id": greentrac_org.id,
                "department_id": installation_dept.id if installation_dept else engineering_dept.id,
                "creator_id": users[0].id,
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now() + timedelta(days=60),
                "status": "in_progress",
                "slug": "solar-installation-lagos-residential",
                "additional_info": {
                    "project_type": "Solar Installation",
                    "location": "Lagos, Nigeria",
                    "customer_type": "Residential",
                    "estimated_budget": 15000000,
                    "currency": "NGN",
                    "team_size": 8,
                    "technologies": ["Solar Panels", "Inverters", "Battery Storage"],
                    "deliverables": ["Installed System", "User Manual", "Warranty Certificate"]
                }
            },
            {
                "name": "Green Energy Awareness Campaign",
                "description": "Comprehensive marketing campaign to promote green energy adoption among residential and commercial customers in Nigeria.",
                "organization_id": greentrac_org.id,
                "department_id": sales_dept.id if sales_dept else None,
                "creator_id": users[1].id,
                "start_date": datetime.now() - timedelta(days=15),
                "end_date": datetime.now() + timedelta(days=45),
                "status": "in_progress",
                "slug": "green-energy-awareness-campaign",
                "additional_info": {
                    "project_type": "Marketing Campaign",
                    "target_audience": "Residential & Commercial",
                    "budget": 5000000,
                    "currency": "NGN",
                    "team_size": 6,
                    "channels": ["Social Media", "Radio", "Print", "Events"],
                    "kpis": ["Lead Generation", "Brand Awareness", "Conversion Rate"]
                }
            },
            {
                "name": "Wind Farm Development - Kano State",
                "description": "Feasibility study and initial development phase for a 50MW wind farm project in Kano State, Nigeria.",
                "organization_id": greentrac_org.id,
                "department_id": engineering_dept.id if engineering_dept else None,
                "creator_id": users[2].id if len(users) > 2 else users[0].id,
                "start_date": datetime.now() - timedelta(days=60),
                "end_date": datetime.now() + timedelta(days=180),
                "status": "in_progress",
                "slug": "wind-farm-kano-state",
                "additional_info": {
                    "project_type": "Wind Energy",
                    "capacity": "50MW",
                    "location": "Kano State, Nigeria",
                    "budget": 200000000,
                    "currency": "NGN",
                    "team_size": 12,
                    "phases": ["Feasibility Study", "Environmental Assessment", "Design", "Construction"],
                    "stakeholders": ["Government", "Local Communities", "Investors"]
                }
            },
            {
                "name": "Customer Portal Mobile App",
                "description": "Development of a mobile application for customers to monitor their energy consumption, manage accounts, and access support services.",
                "organization_id": greentrac_org.id,
                "department_id": engineering_dept.id if engineering_dept else None,
                "creator_id": users[0].id,
                "start_date": datetime.now() - timedelta(days=90),
                "end_date": datetime.now() + timedelta(days=120),
                "status": "in_progress",
                "slug": "customer-portal-mobile-app",
                "additional_info": {
                    "project_type": "Mobile Application",
                    "platform": "iOS & Android",
                    "budget": 8000000,
                    "currency": "NGN",
                    "team_size": 5,
                    "technologies": ["React Native", "Node.js", "PostgreSQL"],
                    "features": ["Energy Monitoring", "Billing", "Support", "Maintenance Requests"]
                }
            },
            {
                "name": "Solar Installation Project - Abuja Commercial",
                "description": "Large-scale commercial solar installation for office buildings in Abuja, including energy storage solutions.",
                "organization_id": greentrac_org.id,
                "department_id": installation_dept.id if installation_dept else engineering_dept.id,
                "creator_id": users[1].id,
                "start_date": datetime.now() + timedelta(days=30),
                "end_date": datetime.now() + timedelta(days=120),
                "status": "not_started",
                "slug": "solar-installation-abuja-commercial",
                "additional_info": {
                    "project_type": "Solar Installation",
                    "location": "Abuja, Nigeria",
                    "customer_type": "Commercial",
                    "estimated_budget": 45000000,
                    "currency": "NGN",
                    "team_size": 10,
                    "technologies": ["Solar Panels", "Inverters", "Battery Storage", "Grid Tie"],
                    "deliverables": ["Installed System", "Energy Monitoring", "Maintenance Plan"]
                }
            }
        ]
        
        # Create projects for EcoFriendly (if organization exists)
        ecofriendly_projects = []
        if ecofriendly_org:
            ecofriendly_projects = [
                {
                    "name": "Environmental Impact Assessment - Lagos Port",
                    "description": "Comprehensive environmental impact assessment for port expansion project in Lagos, including marine and terrestrial impact evaluation.",
                    "organization_id": ecofriendly_org.id,
                    "department_id": environmental_dept.id if environmental_dept else None,
                    "creator_id": users[2].id if len(users) > 2 else users[0].id,
                    "start_date": datetime.now() - timedelta(days=45),
                    "end_date": datetime.now() + timedelta(days=90),
                    "status": "in_progress",
                    "slug": "eia-lagos-port-expansion",
                    "additional_info": {
                        "project_type": "Environmental Assessment",
                        "location": "Lagos Port, Nigeria",
                        "budget": 12000000,
                        "currency": "NGN",
                        "team_size": 8,
                        "scope": ["Marine Impact", "Terrestrial Impact", "Air Quality", "Noise"],
                        "deliverables": ["EIA Report", "Mitigation Plan", "Monitoring Protocol"]
                    }
                },
                {
                    "name": "Sustainable Waste Management Research",
                    "description": "Research project to develop innovative waste management solutions for urban areas in Nigeria, focusing on recycling and waste-to-energy technologies.",
                    "organization_id": ecofriendly_org.id,
                    "department_id": rnd_dept.id if rnd_dept else None,
                    "creator_id": users[3].id if len(users) > 3 else users[0].id,
                    "start_date": datetime.now() - timedelta(days=30),
                    "end_date": datetime.now() + timedelta(days=150),
                    "status": "in_progress",
                    "slug": "sustainable-waste-management-research",
                    "additional_info": {
                        "project_type": "Research & Development",
                        "focus_area": "Waste Management",
                        "budget": 15000000,
                        "currency": "NGN",
                        "team_size": 6,
                        "technologies": ["Waste-to-Energy", "Recycling", "Biogas"],
                        "deliverables": ["Research Report", "Pilot Project", "Implementation Guide"]
                    }
                }
            ]
        
        all_projects = greentrac_projects + ecofriendly_projects
        created_projects = []
        
        # Create projects
        for project_data in all_projects:
            existing_project = Project.fetch_one_by_field(
                db=db,
                throw_error=False,
                slug=project_data['slug']
            )
            
            if not existing_project:
                new_project = Project.create(
                    db=db,
                    **project_data
                )
                created_projects.append(new_project)
                print(f"Project '{new_project.name}' created")
                
                # Create project members
                # Add creator as owner
                owner_member_data = {
                    "user_id": new_project.creator_id,
                    "project_id": new_project.id,
                    "role": "owner",
                    "is_active": True
                }
                
                existing_owner = ProjectMember.fetch_one_by_field(
                    db=db,
                    throw_error=False,
                    user_id=new_project.creator_id,
                    project_id=new_project.id
                )
                
                if not existing_owner:
                    ProjectMember.create(
                        db=db,
                        **owner_member_data
                    )
                    print(f"  - Added owner: {new_project.creator.first_name} {new_project.creator.last_name}")
                
                # Add additional team members
                num_additional_members = min(3, len(users) - 1)
                for i in range(1, num_additional_members + 1):
                    if i < len(users):
                        member_user = users[i]
                        role = "admin" if i == 1 else "member"
                        
                        member_data = {
                            "user_id": member_user.id,
                            "project_id": new_project.id,
                            "role": role,
                            "is_active": True
                        }
                        
                        existing_member = ProjectMember.fetch_one_by_field(
                            db=db,
                            throw_error=False,
                            user_id=member_user.id,
                            project_id=new_project.id
                        )
                        
                        if not existing_member:
                            ProjectMember.create(
                                db=db,
                                **member_data
                            )
                            print(f"  - Added {role}: {member_user.first_name} {member_user.last_name}")
                
                # Create milestones for some projects
                if "Solar Installation" in new_project.name:
                    milestones_data = [
                        {
                            "project_id": new_project.id,
                            "name": "Site Survey Complete",
                            "description": "Complete site survey and assessment",
                            "due_date": new_project.start_date + timedelta(days=10)
                        },
                        {
                            "project_id": new_project.id,
                            "name": "System Design Approved",
                            "description": "Solar system design approved by customer",
                            "due_date": new_project.start_date + timedelta(days=20)
                        },
                        {
                            "project_id": new_project.id,
                            "name": "Installation Complete",
                            "description": "Physical installation of solar panels and equipment",
                            "due_date": new_project.start_date + timedelta(days=45)
                        },
                        {
                            "project_id": new_project.id,
                            "name": "Commissioning & Testing",
                            "description": "System commissioning, testing, and customer handover",
                            "due_date": new_project.start_date + timedelta(days=55)
                        }
                    ]
                    
                    for milestone_data in milestones_data:
                        existing_milestone = Milestone.fetch_one_by_field(
                            db=db,
                            throw_error=False,
                            name=milestone_data['name'],
                            project_id=new_project.id
                        )
                        
                        if not existing_milestone:
                            Milestone.create(
                                db=db,
                                **milestone_data
                            )
                            print(f"  - Milestone created: {milestone_data['name']}")
                
                elif "Mobile App" in new_project.name:
                    milestones_data = [
                        {
                            "project_id": new_project.id,
                            "name": "UI/UX Design Complete",
                            "description": "Complete user interface and user experience design",
                            "due_date": new_project.start_date + timedelta(days=30)
                        },
                        {
                            "project_id": new_project.id,
                            "name": "Backend API Development",
                            "description": "Complete backend API development and testing",
                            "due_date": new_project.start_date + timedelta(days=60)
                        },
                        {
                            "project_id": new_project.id,
                            "name": "Mobile App Beta Release",
                            "description": "Beta version of mobile application released",
                            "due_date": new_project.start_date + timedelta(days=90)
                        },
                        {
                            "project_id": new_project.id,
                            "name": "Production Release",
                            "description": "Production release of mobile application",
                            "due_date": new_project.start_date + timedelta(days=120)
                        }
                    ]
                    
                    for milestone_data in milestones_data:
                        existing_milestone = Milestone.fetch_one_by_field(
                            db=db,
                            throw_error=False,
                            name=milestone_data['name'],
                            project_id=new_project.id
                        )
                        
                        if not existing_milestone:
                            Milestone.create(
                                db=db,
                                **milestone_data
                            )
                            print(f"  - Milestone created: {milestone_data['name']}")
                
            else:
                print(f"Project '{existing_project.name}' already exists")
        
        print(f"Total projects created: {len(created_projects)}")


if __name__ == "__main__":
    seed_projects()