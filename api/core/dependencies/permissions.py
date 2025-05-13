from typing import Dict, List


ORG_PERMS = [
    "organization:delete", "organization:view", "organization:update", "organization:revoke-invite",
    "organization:invite-user", "organization:manage-members", "organization:view-members",
    "department:create", "department:update", "department:view", "department:delete",
    "location:create", "location:update", "location:delete", "location:view", "contact_info:create",
    "contact_info:update", "contact_info:delete", "contact_info:view", "role:create",
    "role:update", "role:delete", "role:view", "organization:assign-role"
    "business-partner:delete", "business-partner:attach-to-user", "business-partner:update", 
    "business-partner:create",
    
]
    
CONTENT_PERMS = [
    "content:create", "content:update", "content:delete",
    "content:publish", "content:schedule", "content:view",
    "content:approve", "content:rollback-version",
    "content-template:create", "content-template:update", "content-template:delete",
]

CAMPAIGN_PERMS = [
    "campaign:create", "campaign:update", "campaign:delete",
    "campaign:view", "campaign:view-analytics", "campaign:manage-budget"
]

BILLING_PERMS = [
    "billing:view", "billing:update-payment", "billing:view-invoices",
    "billing:download-receipts"
]

REPORT_PERMS = [
    "report:generate", "report:view", "report:export"
]

APIKEY_PERMS = [
    "apikey:create", "apikey:view", "apikey:delete"
]

FILE_PERMS = [
    "file:upload", "file:update", "file:delete", "file:view",
    "folder:create", "folder:update", "folder:delete", "folder:view",
]

FORM_PERMS = [
    "form:create", "form:view", "form:update", "form:delete",
    "form:view-responses", "form-template:create", "form-template:update",
    "form-template:delete", 
]

EMAIL_TEMPLATE_PERMS = [
    "template:create", "template:update", "template:delete",
    "layout:create", "layout:update", "layout:delete",
    "email:send", "email:receive"
]

PROJECT_PERMS = [
    "project:create", "project:update", "project:delete",
    "project:assign-member", "project:update-member",
    "task:create", "task:update", "task:delete",
    "task:assign-member", "task:update-member",
    "milestone:create", "milestone:update", "milestone:delete"
]

PRODUCT_AND_SALES_PERMS = [
    "product:create", "product:update", "product:delete",
    "product-variant:create", "product-variant:update", "product-variant:delete",
    "sale:create", "sale:update", "sale:delete",
    "order:create", "order:update", "order:delete",
    "inventory:create", "inventory:update", "inventory:delete",
    "price:create", "price:update", "price:delete",
    "vendor:create", "vendor:update", "vendor:delete",
    "customer:create", "customer:update", "customer:delete",
]

CATEGORY_PERMS = [
    "category:create", "category:update", "category:delete",
]

FINANCIAL_PERMS = [
    "invoice:create", "invoice:update", "invoice:delete",
    "refund:create", "refund:update", "refund:delete",
    "payment:create", "payment:update", "payment:delete",
]

# Combined permission groups
ADMIN_PERMS = (
    ORG_PERMS + CONTENT_PERMS + CAMPAIGN_PERMS + 
    BILLING_PERMS + REPORT_PERMS + APIKEY_PERMS + 
    FILE_PERMS + FORM_PERMS + EMAIL_TEMPLATE_PERMS +
    PROJECT_PERMS + PRODUCT_AND_SALES_PERMS + FINANCIAL_PERMS +
    CATEGORY_PERMS
)
CONTENT_MANAGER_PERMS = CONTENT_PERMS + CAMPAIGN_PERMS + REPORT_PERMS + EMAIL_TEMPLATE_PERMS[6:]  # allow email sending
EDITOR_PERMS = CONTENT_PERMS[:5]  # Exclude approve
AGENT_PREMS = PRODUCT_AND_SALES_PERMS + FINANCIAL_PERMS + CATEGORY_PERMS + REPORT_PERMS + EMAIL_TEMPLATE_PERMS[6:]

# Role to permissions mapping
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    # System roles
    "Superadmin": ["*"],  # Wildcard for all permissions
    "System Auditor": REPORT_PERMS + ["logs:view"],
    
    # Organization roles
    "Owner": ADMIN_PERMS,
    "Admin": ADMIN_PERMS[1:],  # All except org:delete
    "Agent": AGENT_PREMS,
    "Content Manager": CONTENT_MANAGER_PERMS,
    "Campaign Manager": CAMPAIGN_PERMS + REPORT_PERMS,
    
    # Content roles
    "Content Editor": EDITOR_PERMS,
    "Content Approver": ["content:approve", "content:view"],
    "Content Creator": CONTENT_PERMS[:3],  # create/edit/delete
    
    "Guest": []
}


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

# DEPARTMENT
# Define all possible department permissions
DEPARTMENT_PERMISSIONS = [
    # Department Structure
    "department:view", "department:create", "department:update", "department:archive", "department:view-hierarchy",
    
    # Member Management
    "department:add-member", "department:remove-member", "department:view-members", "department:assign-role",
    "department:create-role", "department:update-role", "department:delete-role", "department:view-role", "department:assign-role",
    
    # Financial
    "department:view-budget", "department:update-budget", "department:request-funds", "department:approve-funds",
    "department:create-budget",
    
    # Operations
    "department:manage-equipment", "department:request-resources", "department:approve-requests",
    
    # Content
    "department:create-content", "department:edit-content", "department:approve-content", "department:publish-content",
    
    # Reporting
    "department:generate-reports", "department:view-analytics", "department:export-data",
    
    # Administration
    "department:edit-settings", "department:view-audit-logs",
    
    # Cross-functional
    "department:initiate-collaboration", "department:approve-collaboration",
    
    # Projects
    "project:create", "project:update", "project:delete",
    "project:assign-member", "project:update-member"
    "task:create", "task:update", "task:delete",
    "task:assign-member", "task:update-member",
    "milestone:create", "milestone:update", "milestone:delete",
]

# Default roles with associated permissions
DEFAULT_DEPARTMENT_ROLES = [
    {
        "name": "Department Head",
        "description": "Full control over department operations and strategy",
        "permissions": [
            "department:view", "department:update", "department:view-hierarchy",
            "department:add-member", "department:remove-member", "department:view-members",
            "department:view-budget", "department:update-budget", "department:approve-funds",
            "department:manage-equipment", "department:approve-requests",
            "department:approve-content", "department:publish-content",
            "department:generate-reports", "department:view-analytics",
            "department:edit-settings", "department:assign-role",
            "department:initiate-collaboration", "department:create-budget",
            "department:create-role", "department:update-role", "department:delete-role", "department:view-role"
        ] + PROJECT_PERMS
    },
    {
        "name": "Department Manager",
        "description": "Day-to-day operational management",
        "permissions": [
            "department:view", "department:view-hierarchy",
            "department:view-members", "department:add-member",
            "department:view-budget", "department:request-funds",
            "department:manage-equipment", "department:request-resources",
            "department:create-content", "department:edit-content",
            "department:generate-reports", "department:create-budget",
            "department:initiate-collaboration",
        ] + PROJECT_PERMS
    },
    {
        "name": "Team Lead",
        "description": "Supervises a team within the department",
        "permissions": [
            "department:view",
            "department:view-members",
            "department:request-resources",
            "department:create-content",
            "department:view-analytics"
        ] + PROJECT_PERMS
    },
    {
        "name": "Content Approver",
        "description": "Specialized role for reviewing and publishing content",
        "permissions": [
            "department:view",
            "department:approve-content",
            "department:publish-content"
        ]
    },
    {
        "name": "Financial Officer",
        "description": "Handles budget and spending approvals",
        "permissions": [
            "department:view",
            "department:view-budget",
            "department:update-budget",
            "department:approve-funds",
            "department:create-budget",
        ]
    },
    {
        "name": "Department Member",
        "description": "Basic access for regular department members",
        "permissions": [
            "department:view",
            "department:request-resources"
        ]
    }
]
