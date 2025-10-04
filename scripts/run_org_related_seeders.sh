#!/bin/bash

SEEDERS_DIR="scripts/seeders"

python3 "$SEEDERS_DIR/seed_org_role_permissions.py"
python3 "$SEEDERS_DIR/seed_template_layouts.py"
python3 "$SEEDERS_DIR/seed_email_templates.py"
python3 "$SEEDERS_DIR/seed_content_templates.py"
python3 "$SEEDERS_DIR/seed_form_templates.py"
python3 "$SEEDERS_DIR/seed_department_role_permissions.py"

