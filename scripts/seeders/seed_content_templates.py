import sys
import pathlib
import os

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.content import ContentTemplate
from api.db.database import get_db_with_ctx_manager

content_templates = [
    {
        "name": "Article",
        "description": "A write up on a topic",
        "content_type": "article"
    },
    {
        "name": "Blog Post",
        "description": "A blog post on a otpic",
        "content_type": "blog_post"
    },
    {
        "name": "Announcement",
        "description": "Announcement for the launch of comethign new",
        "content_type": "announcement"
    },
    {
        "name": "Advertisement",
        "description": "Advertisement for an activity or entity",
        "content_type": "advertisement"
    },
    {
        "name": "Landing Page",
        "description": "Landing page to introduce a new entity like a product",
        "content_type": "landing_page"
    },
    {
        "name": "Press Release",
        "description": "Press release concerning an accouncement",
        "content_type": "press_release"
    },
    {
        "name": "Case Study",
        "description": "Case study showcasing something",
        "content_type": "case_study"
    },
    {
        "name": "White Paper",
        "description": "White paper discussing a topic",
        "content_type": "white_paper"
    },
    {
        "name": "Product Update",
        "description": "Update on the new features and changes in product",
        "content_type": "product_update"
    },
    {
        "name": "Video",
        "description": "Video explaining how to perform an action effectively",
        "content_type": "video"
    },
    {
        "name": "Podcast",
        "description": "Podcast episode recording",
        "content_type": "podcast"
    },
    {
        "name": "Testimonial",
        "description": "Testimonial from a customer",
        "content_type": "testimonial"
    },
    {
        "name": "FAQ - Frequently Asked Questions",
        "description": "Frequently asked questions and their answers",
        "content_type": "faq"
    },
    {
        "name": "Knowledge Base",
        "description": "A knowledge base article providing steps in solving a problem",
        "content_type": "knowledge_base"
    },
    {
        "name": "Event",
        "description": "Event announcement for an activity",
        "content_type": "event"
    },
    {
        "name": "Job Post",
        "description": "Job posting for a position",
        "content_type": "job_post"
    },
    {
        "name": "News",
        "description": "News article concerning an event or activity",
        "content_type": "news"
    },
    {
        "name": "Webinar",
        "description": "Webinar invitation for a session",
        "content_type": "webinar"
    }
]

def seed_content_templates():
    '''Seed content templates'''
    
    with get_db_with_ctx_manager() as db:
        content_templates_dir = f"{ROOT_DIR}/templates/content/default"
            
        for template in content_templates:    
            with open(f"{content_templates_dir}/{template['content_type']}.html", "r") as file:
                html = file.read()
                
            existing_template = ContentTemplate.fetch_one_by_field(
                db=db, throw_error=False,
                name=template['name'],
                content_type=template['content_type'],
                organization_id='-1'
            )
            
            if not existing_template:
                # Store template in db
                new_template = ContentTemplate.create(
                    db=db,
                    name=template['name'],
                    content_type=template['content_type'],
                    description=template['description'],
                    body=html,
                    organization_id='-1'
                )
                print(f"ContentTemplate {new_template.name} created")
            
            else:
                # Update template
                updated_template = ContentTemplate.update(
                    db=db, id=existing_template.id,
                    body=html,
                    description=template['description']
                )
                print(f"ContentTemplate {updated_template.name} updated")
    

if __name__ == "__main__":
    seed_content_templates()
