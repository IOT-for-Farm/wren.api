import sys
import pathlib
import os

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent

# ADD PROJECT ROOT TO IMPORT SEARCH SCOPE
sys.path.append(str(ROOT_DIR))

from api.v1.models.layout import Layout
from api.db.database import get_db


db = next(get_db())

def seed_template_layouts():
    '''Seed template layouts'''
    
    layouts_dir = f"{ROOT_DIR}/templates/email/default/layouts"
    
    layout_html_files = os.listdir(layouts_dir)
    
    for html_file in layout_html_files:
        with open(f"{layouts_dir}/{html_file}", "r") as file:
            html = file.read()
            
        existing_layout = Layout.fetch_one_by_field(
            db=db, throw_error=False,
            name=html_file.split('.')[0],
            feature='email',
            organization_id='-1'
        )
        
        if not existing_layout:
            # Store layout in db
            layout = Layout.create(
                db=db,
                name=html_file.split('.')[0],
                layout=html,
                feature='email',
                organization_id='-1'
            )
            print(f"Layout {layout.name} created")
        
        else:
            # Update layout
            layout = Layout.update(
                db=db, id=existing_layout.id,
                layout=html
            )
            print(f"Layout {layout.name} updated")
    

if __name__ == "__main__":
    seed_template_layouts()
