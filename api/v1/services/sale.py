from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from api.utils.loggers import create_logger
from api.v1.models.sale import Sale
from api.v1.models.vendor import Vendor
from api.v1.schemas import sale as sale_schemas


logger = create_logger(__name__)

class SaleService:
    
    @classmethod
    def extract_monthly_sale_data_for_vendor(
        cls,
        db: Session,
        organization_id: str,
        vendor_id: str,
        month: int = None,
        year: int = None,
    ):
        '''This function extracts monthly sale data foe a vendor'''
        
        vendor = Vendor.fetch_one_by_field(
            db=db,
            business_partner_id=vendor_id
        )
        
        year = datetime.now().year if not year else year
        month = datetime.now().month if not month else month
        
        # Full month name
        month_str = datetime(year, month, 1).strftime('%B')  # "January" to "December"
        
        start_date = datetime(year, month, 1)
        end_date =start_date + timedelta(days=30)
        
        # Fetch vendor sales
        query = db.query(Sale).filter(
            Sale.organization_id == organization_id,
            Sale.vendor_id == vendor.id,
            Sale.is_deleted == False,
        ).filter(
            and_(
                Sale.created_at >= start_date,
                Sale.created_at <= end_date    
            )
        )
        
        sale_count = query.count()
        sales = query.all()
        
        total_price = sum([sale.total_price_of_sale for sale in sales])
        total_commission_owed = sum([sale.organization_profit for sale in sales])
        total_profit = sum([sale.vendor_profit for sale in sales])
        total_items_sold = sum([sale.quantity for sale in sales])
        
        product_sale_data = [
            {
                "product_name": sale.product.name,
                "price": sale.product.price.selling_price if sale.product.price else 0.00,
                "quantity_sold": sale.quantity,
                "date_sold": sale.created_at,
                "total_price_of_sale": sale.total_price_of_sale,
                "profit_on_sale": sale.vendor_profit,
                "commission_owed_on_sale": sale.organization_profit
            } for sale in sales
        ]
        
        final_data = {
            'product_sale_data': product_sale_data,
            'total_commission_owed': total_commission_owed,
            'total_profit': total_profit,
            'total_items_sold': total_items_sold,
            'total_sales': sale_count,
            'total_price': total_price,
            "commission_percentage": vendor.commission_percentage,
            "currency_code": [sale.currency_code for sale in sales][0]
        }
        
        return final_data
