import random
import sys
import pathlib
import os

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.template import Template
from api.v1.models.layout import Layout
from api.db.database import get_db_with_ctx_manager

def seed_email_templates():
    '''Seed e,ail templates '''
    
    with get_db_with_ctx_manager() as db:
        templates_dir = f"{ROOT_DIR}/templates/email/default/templates"
        
        template_html_files = os.listdir(templates_dir)
        
        for html_file in template_html_files:
            with open(f"{templates_dir}/{html_file}", "r") as file:
                html = file.read()
                
            existing_template = Template.fetch_one_by_field(
                db=db, throw_error=False,
                name=html_file.split('.')[0],
                feature='email',
                organization_id='-1'
            )
            
            if not existing_template:
                # Get all layouts
                query, layouts, count = Layout.fetch_by_field(
                    db=db,
                    paginate=False,
                    organization_id='-1',
                    feature='email'
                )
                
                # Choose a random layout id
                layout_id = random.choice([layout.id for layout in layouts])
                
                # Store template in db
                template = Template.create(
                    db=db,
                    name=html_file.split('.')[0],
                    subject=html_file.split('.')[0].replace('-', ' ').capitalize(),
                    body=html,
                    feature='email',
                    organization_id='-1',
                    layout_id=layout_id
                )
                print(f"Template {template.name} created")
            
            else:
                # Update template
                template = Template.update(
                    db=db, id=existing_template.id,
                    body=html
                )
                print(f"Template {template.name} updated")
        

if __name__ == "__main__":
    seed_email_templates()
