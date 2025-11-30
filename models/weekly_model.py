from datetime import datetime
from pydantic import BaseModel, field_serializer
from typing import List

class WeeklyDay(BaseModel):
    date: str
    spent: float

class WeeklyResponse(BaseModel):
    weekly_id: str
    user_id: str
    type: str
    days: List[WeeklyDay]
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", mode="plain", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%Y/%m/%d %H:%M:%S")
