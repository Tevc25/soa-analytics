import os
import requests
from datetime import datetime, timedelta
from db_two.database import get_db

CATEGORY_BUDGET_URL = os.getenv("CATEGORY_BUDGET_URL", "http://localhost:8002").rstrip("/")

class WeeklyService:
    def __init__(self):
        self.db = get_db()
        self.col = self.db["weekly_data"]

    def _parse_iso(self, s):
        try:
            return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        except Exception:
            return None

    def generate_last7days(self, user_id: str):
        today = datetime.now()
        start = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = (today + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        keys = []
        for i in range(7):
            keys.append((start + timedelta(days=i)).strftime("%Y-%m-%d"))

        spent_by_day = {k: 0.0 for k in keys}

        rc = requests.get(f"{CATEGORY_BUDGET_URL}/{user_id}/categories", timeout=8)
        if rc.status_code != 200:
            raise ValueError(f"Category service error: {rc.status_code}")

        categories = rc.json()

        for c in categories:
            for it in c.get("items", []) or []:
                dt = self._parse_iso(it.get("created_at"))
                if not dt:
                    continue
                if start <= dt < end:
                    k = dt.strftime("%Y-%m-%d")
                    if k in spent_by_day:
                        price = float(it.get("item_price", 0))
                        qty = int(it.get("item_quantity", 1))
                        spent_by_day[k] += price * qty

        days = [{"date": k, "spent": spent_by_day[k]} for k in keys]

        now = datetime.now()
        existing = self.col.find_one({"user_id": user_id, "type": "last7days"})

        if existing:
            self.col.update_one(
                {"_id": existing["_id"]},
                {"$set": {"days": days, "updated_at": now}}
            )
            return {"message": "Weekly analytics updated", "weekly_id": str(existing["_id"])}

        doc = {
            "user_id": user_id,
            "type": "last7days",
            "days": days,
            "created_at": now,
            "updated_at": now
        }
        res = self.col.insert_one(doc)
        return {"message": "Weekly analytics generated", "weekly_id": str(res.inserted_id)}

    def get_last7days(self, user_id: str):
        doc = self.col.find_one({"user_id": user_id, "type": "last7days"})
        if not doc:
            raise ValueError("Weekly analytics not found")

        return {
            "weekly_id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "type": doc.get("type", "last7days"),
            "days": doc.get("days", []),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }

    def delete_last7days(self, user_id: str):
        res = self.col.delete_one({"user_id": user_id, "type": "last7days"})
        if res.deleted_count == 0:
            raise ValueError("Weekly analytics not found")
        return {"message": "Weekly analytics deleted"}
