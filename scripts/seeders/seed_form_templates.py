import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.db.database import get_db_with_ctx_manager
from api.v1.models.form import FormTemplate

# Define the default form templates
form_templates = [
    {
        "template_name": "Default Form",
        "purpose": "This is a default form template.",
        "fields": [
            {"label": "Name", "name": "name", "type": "text", "required": True, "placeholder": "Enter your name"},
            {"label": "Email", "name": "email", "type": "email", "required": True, "placeholder": "Enter your email"},
            {"label": "Message", "name": "message", "type": "textarea", "required": True, "placeholder": "Your message"},
        ],
    },
    {
        "template_name": "Contact Form",
        "purpose": "To collect general contact messages from visitors.",
        "fields": [
            {"label": "Full Name", "name": "full_name", "type": "text", "required": True, "placeholder": "John Doe"},
            {"label": "Email Address", "name": "email", "type": "email", "required": True, "placeholder": "you@example.com"},
            {"label": "Phone Number", "name": "phone", "type": "tel", "required": False, "placeholder": "08012345678"},
            {"label": "Subject", "name": "subject", "type": "text", "required": True, "placeholder": "Subject of your message"},
            {"label": "Message", "name": "message", "type": "textarea", "required": True, "placeholder": "Write your message here..."},
        ],
    },
    {
        "template_name": "Newsletter Form",
        "purpose": "To subscribe users to the newsletter.",
        "fields": [
            {"label": "Name", "name": "name", "type": "text", "required": True, "placeholder": "Your name"},
            {"label": "Email", "name": "email", "type": "email", "required": True, "placeholder": "Your email"},
        ],
    },
    {
        "template_name": "Feedback Form",
        "purpose": "To collect user feedback and ratings.",
        "fields": [
            {"label": "Feedback", "name": "feedback", "type": "textarea", "required": True, "placeholder": "Write your feedback"},
            {"label": "Rating", "name": "rating", "type": "number", "min": 1, "max": 5, "required": True, "placeholder": "Rate us (1-5)"},
        ],
    },
    {
        "template_name": "Job Application Form",
        "purpose": "To apply for available positions.",
        "fields": [
            {"label": "Full Name", "name": "full_name", "type": "text", "required": True, "placeholder": "Your name"},
            {"label": "Email", "name": "email", "type": "email", "required": True},
            {"label": "Phone Number", "name": "phone", "type": "tel", "required": True},
            {"label": "Resume", "name": "resume", "type": "file", "accept": ".pdf,.doc,.docx", "required": True},
            {"label": "Cover Letter", "name": "cover_letter", "type": "textarea", "required": False, "placeholder": "Optional cover letter"},
            {"label": "Position", "name": "position", "type": "select", "required": True, "options": ["Frontend Developer", "Backend Developer", "Designer", "Marketing"]},
        ],
    },
    {
        "template_name": "Event Registration Form",
        "purpose": "To register attendees for an event.",
        "fields": [
            {"label": "Full Name", "name": "name", "type": "text", "required": True},
            {"label": "Email", "name": "email", "type": "email", "required": True},
            {"label": "Phone", "name": "phone", "type": "tel", "required": True},
            {"label": "Select Session", "name": "session", "type": "select", "required": True, "options": ["Morning", "Afternoon", "Evening"]},
            {"label": "Meal Preference", "name": "meal", "type": "radio", "options": ["Vegetarian", "Non-Vegetarian", "Vegan"], "required": True},
        ],
    },
    {
        "template_name": "Support Ticket Form",
        "purpose": "To open support requests or complaints.",
        "fields": [
            {"label": "Name", "name": "name", "type": "text", "required": True},
            {"label": "Email", "name": "email", "type": "email", "required": True},
            {"label": "Issue Type", "name": "issue_type", "type": "select", "required": True, "options": ["Billing", "Technical", "General"]},
            {"label": "Urgency", "name": "urgency", "type": "radio", "options": ["Low", "Medium", "High"], "required": True},
            {"label": "Message", "name": "message", "type": "textarea", "required": True},
        ],
    }
]


def seed_form_templates():
    """Seed default form templates into the database."""
    
    with get_db_with_ctx_manager() as db:
        for template in form_templates:
            # Check if the form template already exists
            existing_template = FormTemplate.fetch_one_by_field(
                db=db, throw_error=False,
                template_name=template['template_name'],
                is_deleted=False,
                organization_id='-1'
            )
            
            if not existing_template:
                # Create a new form template
                FormTemplate.create(
                    db=db,
                    organization_id='-1',
                    **template
                )
                
                print(f'New form template: {template["template_name"]} created')
            
            else:
                # Update the existing form template
                FormTemplate.update(
                    db=db,
                    id=existing_template.id,
                    **template
                )
                
                print(f'Form template: {template["template_name"]} updated')
            

if __name__ == "__main__":
    seed_form_templates()
