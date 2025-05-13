from fastapi import APIRouter

from api.v1.routes.auth import auth_router
from api.v1.routes.user import user_router
from api.v1.routes.organization import organization_router
from api.v1.routes.file import file_router
from api.v1.routes.form import form_router
from api.v1.routes.apikey import apikey_router
from api.v1.routes.contact_info import contact_info_router
from api.v1.routes.department import department_router
from api.v1.routes.location import location_router
from api.v1.routes.tag import tag_router
from api.v1.routes.template import template_router
from api.v1.routes.layout import layout_router
from api.v1.routes.comment import comment_router
from api.v1.routes.review import review_router
from api.v1.routes.project import project_router
from api.v1.routes.content import content_router
from api.v1.routes.content_template import content_template_router
from api.v1.routes.category import category_router
from api.v1.routes.product import product_router
from api.v1.routes.customer import customer_router
from api.v1.routes.vendor import vendor_router
from api.v1.routes.inventory import inventory_router
from api.v1.routes.invoice import invoice_router
from api.v1.routes.order import order_router
from api.v1.routes.sale import sale_router
from api.v1.routes.account import account_router
from api.v1.routes.payment import payment_router
from api.v1.routes.price import price_router
from api.v1.routes.product_variant import product_variant_router
from api.v1.routes.business_partner import business_partner_router

v1_router = APIRouter(prefix='/api/v1')

# Register all routes
v1_router.include_router(auth_router)
v1_router.include_router(user_router)
v1_router.include_router(organization_router)
v1_router.include_router(apikey_router)
v1_router.include_router(department_router)
v1_router.include_router(content_router)
v1_router.include_router(content_template_router)
v1_router.include_router(project_router)
v1_router.include_router(product_router)
v1_router.include_router(product_variant_router)
v1_router.include_router(price_router)
v1_router.include_router(business_partner_router)
v1_router.include_router(vendor_router)
v1_router.include_router(customer_router)
v1_router.include_router(inventory_router)
v1_router.include_router(invoice_router)
v1_router.include_router(order_router)
v1_router.include_router(sale_router)
v1_router.include_router(account_router)
v1_router.include_router(payment_router)
v1_router.include_router(template_router)
v1_router.include_router(layout_router)
v1_router.include_router(file_router)
v1_router.include_router(form_router)
v1_router.include_router(tag_router)
v1_router.include_router(category_router)
v1_router.include_router(contact_info_router)
v1_router.include_router(location_router)
v1_router.include_router(comment_router)
v1_router.include_router(review_router)
