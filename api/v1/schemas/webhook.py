from pydantic import BaseModel
from typing import Optional


class WebhookBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateWebhook(BaseModel):

    unique_id: Optional[str] = None


