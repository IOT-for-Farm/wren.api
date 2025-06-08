from pydantic import BaseModel, EmailStr
from typing import List, Optional


class ReceiptBase(BaseModel):

    unique_id: Optional[str] = None
    
    organization_id: str
    invoice_id: str
    
    amount: float
    payment_method: str
    transaction_reference: Optional[str] = None
    
    template_id: Optional[str] = None
    send_notification: Optional[bool] = True


class GenerateReceipt(BaseModel):
    
    unique_id: Optional[str] = None
    
    organization_id: str
    invoice_id: str
    
    transaction_reference: Optional[str] = None
    
    template_id: Optional[str] = None
    context: Optional[dict] = None
    send_notification: Optional[bool] = True
    recipients: Optional[List[EmailStr]] = None
    

class UpdateReceipt(BaseModel):

    unique_id: Optional[str] = None
