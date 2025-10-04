import sys
import pathlib
from datetime import datetime, timedelta

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.project import Task, TaskAssignee
from api.v1.models.project import Project
from api.v1.models.user import User
from api.db.database import get_db_with_ctx_manager


def seed_tasks():
    '''Seed tasks and task assignees'''
    
    with get_db_with_ctx_manager() as db:
        # Get required dependencies
        projects = Project.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        users = User.fetch_by_field(
            db=db,
            paginate=False
        )[1]  # Get the results, not the query
        
        if not projects or not users:
            print("Required dependencies not found. Please run seed_projects.py and seed_users.py first.")
            return
        
        created_tasks = []
        
        for project in projects:
            # Create tasks for each project
            tasks_data = []
            
            if "Solar Installation" in project.name:
                tasks_data = [
                    {
                        "project_id": project.id,
                        "creator_id": users[0].id,
                        "parent_id": None,
                        "name": "Site Survey and Assessment",
                        "description": "Conduct detailed site survey to assess roof condition, sun exposure, and structural requirements for solar panel installation.",
                        "priority": "high",
                        "status": "completed",
                        "due_date": project.start_date + timedelta(days=5),
                        "additional_info": {
                            "estimated_hours": 8,
                            "required_tools": ["Measuring tape", "Drone", "Structural assessment kit"],
                            "deliverables": ["Site survey report", "Structural assessment", "Solar potential analysis"]
                        }
                    },
                    {
                        "project_id": project.id,
                        "creator_id": users[0].id,
                        "parent_id": None,
                        "name": "Design Solar System Layout",
                        "description": "Create detailed design for solar panel placement, inverter positioning, and electrical connections.",
                        "priority": "high",
                        "status": "in_progress",
                        "due_date": project.start_date + timedelta(days=15),
                        "additional_info": {
                            "estimated_hours": 16,
                            "required_tools": ["CAD software", "Solar design software"],
                            "deliverables": ["System layout diagram", "Electrical schematic", "Equipment specifications"]
                        }
                    },
                    {
                        "project_id": project.id,
                        "creator_id": users[1].id,
                        "parent_id": None,
                        "name": "Procurement of Materials",
                        "description": "Source and procure all required solar panels, inverters, mounting hardware, and electrical components.",
                        "priority": "medium",
                        "status": "pending",
                        "due_date": project.start_date + timedelta(days=20),
                        "additional_info": {
                            "estimated_hours": 12,
                            "required_tools": ["Procurement system", "Vendor contacts"],
                            "deliverables": ["Purchase orders", "Delivery schedule", "Quality certifications"]
                        }
                    },
                    {
                        "project_id": project.id,
                        "creator_id": users[2].id,
                        "parent_id": None,
                        "name": "Installation Execution",
                        "description": "Execute the physical installation of solar panels, inverters, and electrical connections according to design specifications.",
                        "priority": "high",
                        "status": "not_started",
                        "due_date": project.start_date + timedelta(days=45),
                        "additional_info": {
                            "estimated_hours": 40,
                            "required_tools": ["Installation tools", "Safety equipment", "Testing equipment"],
                            "deliverables": ["Installed system", "Installation photos", "Test results"]
                        }
                    }
                ]
            elif "Awareness Campaign" in project.name:
                tasks_data = [
                    {
                        "project_id": project.id,
                        "creator_id": users[1].id,
                        "parent_id": None,
                        "name": "Campaign Strategy Development",
                        "description": "Develop comprehensive marketing strategy for green energy awareness campaign targeting residential customers.",
                        "priority": "high",
                        "status": "completed",
                        "due_date": project.start_date + timedelta(days=3),
                        "additional_info": {
                            "estimated_hours": 12,
                            "required_tools": ["Market research data", "Strategy templates"],
                            "deliverables": ["Campaign strategy document", "Target audience analysis", "Channel recommendations"]
                        }
                    },
                    {
                        "project_id": project.id,
                        "creator_id": users[1].id,
                        "parent_id": None,
                        "name": "Content Creation",
                        "description": "Create engaging content for social media, radio, and print materials to promote green energy benefits.",
                        "priority": "medium",
                        "status": "in_progress",
                        "due_date": project.start_date + timedelta(days=10),
                        "additional_info": {
                            "estimated_hours": 20,
                            "required_tools": ["Design software", "Video editing tools", "Content management system"],
                            "deliverables": ["Social media posts", "Radio scripts", "Print materials", "Video content"]
                        }
                    },
                    {
                        "project_id": project.id,
                        "creator_id": users[3].id if len(users) > 3 else users[0].id,
                        "parent_id": None,
                        "name": "Community Event Planning",
                        "description": "Plan and organize community events in Lagos and Abuja to engage residents and promote green energy adoption.",
                        "priority": "medium",
                        "status": "pending",
                        "due_date": project.start_date + timedelta(days=25),
                        "additional_info": {
                            "estimated_hours": 16,
                            "required_tools": ["Event planning software", "Venue contacts"],
                            "deliverables": ["Event schedule", "Venue bookings", "Participant registration system"]
                        }
                    }
                ]
            elif "Wind Farm" in project.name:
                tasks_data = [
                    {
                        "project_id": project.id,
                        "creator_id": users[2].id,
                        "parent_id": None,
                        "name": "Wind Resource Assessment",
                        "description": "Conduct comprehensive wind resource assessment at proposed site locations in Kano State.",
                        "priority": "high",
                        "status": "in_progress",
                        "due_date": project.start_date + timedelta(days=30),
                        "additional_info": {
                            "estimated_hours": 24,
                            "required_tools": ["Wind measurement equipment", "Data analysis software"],
                            "deliverables": ["Wind resource report", "Wind speed data", "Energy production estimates"]
                        }
                    },
                    {
                        "project_id": project.id,
                        "creator_id": users[2].id,
                        "parent_id": None,
                        "name": "Environmental Impact Study",
                        "description": "Conduct environmental impact assessment to evaluate effects on local ecosystem and wildlife.",
                        "priority": "high",
                        "status": "pending",
                        "due_date": project.start_date + timedelta(days=45),
                        "additional_info": {
                            "estimated_hours": 32,
                            "required_tools": ["Environmental monitoring equipment", "GIS software"],
                            "deliverables": ["Environmental impact report", "Mitigation recommendations", "Regulatory compliance checklist"]
                        }
                    }
                ]
            elif "Mobile App" in project.name:
                tasks_data = [
                    {
                        "project_id": project.id,
                        "creator_id": users[0].id,
                        "parent_id": None,
                        "name": "UI/UX Design",
                        "description": "Design user interface and user experience for the customer portal mobile application.",
                        "priority": "high",
                        "status": "pending",
                        "due_date": project.start_date + timedelta(days=14),
                        "additional_info": {
                            "estimated_hours": 40,
                            "required_tools": ["Figma", "Adobe XD", "Prototyping tools"],
                            "deliverables": ["Wireframes", "UI designs", "Interactive prototypes"]
                        }
                    },
                    {
                        "project_id": project.id,
                        "creator_id": users[0].id,
                        "parent_id": None,
                        "name": "Backend API Development",
                        "description": "Develop backend APIs for energy monitoring, user management, and payment integration.",
                        "priority": "high",
                        "status": "pending",
                        "due_date": project.start_date + timedelta(days=45),
                        "additional_info": {
                            "estimated_hours": 60,
                            "required_tools": ["Node.js", "Database", "API testing tools"],
                            "deliverables": ["REST APIs", "Database schema", "API documentation"]
                        }
                    }
                ]
            
            # Create tasks for this project
            for task_data in tasks_data:
                existing_task = Task.fetch_one_by_field(
                    db=db,
                    throw_error=False,
                    name=task_data['name'],
                    project_id=project.id
                )
                
                if not existing_task:
                    new_task = Task.create(
                        db=db,
                        **task_data
                    )
                    created_tasks.append(new_task)
                    print(f"Task '{new_task.name}' created for project '{project.name}'")
                    
                    # Create task assignees
                    if new_task.status != "completed":
                        # Assign to creator and one other user
                        assignee_users = [users[0]]  # Creator
                        if len(users) > 1:
                            assignee_users.append(users[1])
                        
                        for assignee_user in assignee_users:
                            existing_assignee = TaskAssignee.fetch_one_by_field(
                                db=db,
                                throw_error=False,
                                task_id=new_task.id,
                                user_id=assignee_user.id
                            )
                            
                            if not existing_assignee:
                                assignee_data = {
                                    "user_id": assignee_user.id,
                                    "task_id": new_task.id,
                                    "is_active": True
                                }
                                
                                new_assignee = TaskAssignee.create(
                                    db=db,
                                    **assignee_data
                                )
                                print(f"  - Task assigned to: {assignee_user.first_name} {assignee_user.last_name}")
                else:
                    print(f"Task '{existing_task.name}' already exists for project '{project.name}'")
        
        print(f"Total tasks created: {len(created_tasks)}")


if __name__ == "__main__":
    seed_tasks()
