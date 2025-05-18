from pydantic import BaseModel
from typing import Optional


class AnalyticsBase(BaseModel):

    unique_id: Optional[str] = None


class UpdateAnalytics(BaseModel):

    unique_id: Optional[str] = None


