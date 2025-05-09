from typing import List, Optional
from fastapi import BackgroundTasks, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session
from jinja2 import Environment, BaseLoader

from api.core.dependencies.email_sending_service import send_email
from api.utils.loggers import create_logger
from api.v1.models.template import Template
from api.v1.schemas import template as template_schemas


logger = create_logger(__name__)

class TemplateService:
    
    @classmethod
    def render_template(
        cls, 
        db: Session, 
        template_id: str, 
        context: dict,
    ):
        """
        Render a template with the given context.
        """
        
        env = Environment(loader=BaseLoader())
        
        # Fetch the template
        template = Template.fetch_by_id(db=db, id=template_id)
        
        # Most times for email templates
        if template.layout:
            layout_body = template.layout.layout
            
            # Render the inner parts of the template ie. subject, body, footer
            rendered_subject = None
            if template.subject:
                rendered_subject = env.from_string(template.subject).render(context)
            
            rendered_footer = None
            if template.footer:
                rendered_footer = env.from_string(template.footer).render(context)
                
            rendered_body = env.from_string(template.body).render(context)
            
            # Render the layout with the data just rendered
            final_html = env.from_string(layout_body).render(
                body=rendered_body,
                subject=rendered_subject,
                footer=rendered_footer,
                **context
            )
            
            return final_html, rendered_subject, rendered_footer, rendered_body
        
        # Useful for sms templates
        else:
            # Render the template body directly
            final_html = env.from_string(template.body).render(context)
        
            return final_html, None, None, final_html
        

    @classmethod
    def send_email_from_template(
        cls, 
        db: Session, 
        bg_tasks: BackgroundTasks,
        organization_id: str, 
        template_id: str, 
        context: dict,
        recipients: List[EmailStr],
        attachments: Optional[List[str]] = None
    ):
        
        # Fetch the template
        template = Template.fetch_by_id(db, template_id)
        
        # Check if the template belongs to the organization
        if template.organization_id != organization_id:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this template"
            )
        
        # Render the template
        html, subject, footer, body = TemplateService.render_template(
            db=db,
            template_id=template_id,
            context=context
        )
        
        # Send email logic here (not implemented in this example)
        bg_tasks.add_task(
            send_email,
            recipients=recipients,
            html_template_string=html,
            subject=subject if subject else "No subject",
            template_data=context,
            apply_default_template_data=False,
            attachments=attachments
        )
        
    
    # @classmethod
    # def get_template_by_tags