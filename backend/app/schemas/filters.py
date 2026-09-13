from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator


class AnalyticsFilters(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    region: Optional[str] = None
    category: Optional[str] = None
    customer_segment: Optional[str] = None
    salesperson: Optional[str] = None

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v, info):
        date_from = info.data.get("date_from")
        if v and date_from and v < date_from:
            raise ValueError("date_to must be on or after date_from")
        return v
