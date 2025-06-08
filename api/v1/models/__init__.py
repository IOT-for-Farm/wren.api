from api.v1.models.user import User
from api.v1.models.token import Token, BlacklistedToken
from api.v1.models.file import File
from api.v1.models.form import FormResponse, FormTemplate, Form
from api.v1.models.apikey import Apikey
from api.v1.models.contact_info import ContactInfo
from api.v1.models.location import Location
from api.v1.models.tag import Tag, TagAssociation
from api.v1.models.template import Template
from api.v1.models.layout import Layout
from api.v1.models.comment import Comment
from api.v1.models.review import Review
from api.v1.models.category import Category, CategoryAssociation
from api.v1.models.product import Product, ProductPrice, ProductVariant
from api.v1.models.inventory import Inventory
from api.v1.models.customer import Customer
from api.v1.models.vendor import Vendor
from api.v1.models.account import Account
from api.v1.models.business_partner import BusinessPartner
from api.v1.models.invoice import Invoice
from api.v1.models.order import Order
from api.v1.models.payment import Payment
from api.v1.models.receipt import Receipt
from api.v1.models.sale import Sale
from api.v1.models.refund import Refund
from api.v1.models.event import Event, EventAttendee, EventReminder
from api.v1.models.activity_log import ActivityLog
from api.v1.models.project import (
    Project, Milestone, ProjectMember,
    Task, TaskAssignee
)
from api.v1.models.department import (
    Department, DepartmentMember,
    DepartmentRole, DepartmentBudget
)
from api.v1.models.organization import (
    Organization, OrganizationMember,
    OrganizationRole, OrganizationInvite,
    OrganizationSecret
)
from api.v1.models.content import (
    Content, ContentAnalytics, ContentPromotion,
    ContentTarget, ContentTemplate,
    ContentTranslation, ContentVersion
)

def register_model_hooks():
    from api.db.database import get_db_with_ctx_manager
    from api.utils.activity_logger import register_activity_logging
    
    with get_db_with_ctx_manager() as db:
        register_activity_logging(Apikey, db)
        register_activity_logging(Template, db)
        register_activity_logging(Layout, db)
        register_activity_logging(Form, db)
        register_activity_logging(FormTemplate, db)
        register_activity_logging(Product, db)
        register_activity_logging(ProductPrice, db)
        register_activity_logging(ProductVariant, db)
        register_activity_logging(Sale, db)
        register_activity_logging(Invoice, db)
        register_activity_logging(Receipt, db)
        register_activity_logging(Inventory, db)
        register_activity_logging(Order, db)
        register_activity_logging(Payment, db)
        register_activity_logging(Refund, db)
        register_activity_logging(Project, db)
        register_activity_logging(Milestone, db)
        register_activity_logging(Task, db)
        register_activity_logging(Department, db)
        register_activity_logging(DepartmentBudget, db)
        register_activity_logging(Content, db)
        register_activity_logging(ContentTemplate, db)
        register_activity_logging(ContentVersion, db)
        register_activity_logging(Account, db)
        register_activity_logging(Event, db)
        register_activity_logging(EventReminder, db)
        register_activity_logging(OrganizationSecret, db)
        register_activity_logging(Review, db)
