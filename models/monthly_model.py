from datetime import datetime
from pydantic import BaseModel, field_serializer
from typing import List

class MonthlyGenerateRequest(BaseModel):
    month: str

class MonthlyRow(BaseModel):
    category_id: str
    category_name: str
    budget: float
    spent: float

class MonthlyResponse(BaseModel):
    monthly_id: str
    user_id: str
    month: str
    rows: List[MonthlyRow]
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", mode="plain", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%Y/%m/%d %H:%M:%S")
