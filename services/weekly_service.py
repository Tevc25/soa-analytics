import logging
import os
import requests
from datetime import datetime, timedelta
from db_two.database import get_db
from logging_utils import get_correlation_id

CATEGORY_BUDGET_URL = os.getenv("CATEGORY_BUDGET_URL", "http://localhost:8002").rstrip("/")

class WeeklyService:
    def __init__(self):
        self.logger = logging.getLogger("soa-analytics")
        self.db = get_db()
        self.col = self.db["weekly_data"]

    def _parse_iso(self, s):
        try:
            return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        except Exception:
            return None

    def generate_last7days(self, user_id: str, jwt_token: str = None):
        today = datetime.now()
        start = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = (today + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        keys = []
        for i in range(7):
            keys.append((start + timedelta(days=i)).strftime("%Y-%m-%d"))

        spent_by_day = {k: 0.0 for k in keys}

        headers = {}
        correlation_id = get_correlation_id()
        if correlation_id:
            headers["X-Correlation-Id"] = correlation_id
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        self.logger.info(
            "Requesting categories for weekly analytics",
            extra={
                "correlation_id": correlation_id,
                "url": f"{CATEGORY_BUDGET_URL}/{user_id}/categories",
                "method": "GET",
            },
        )
        rc = requests.get(f"{CATEGORY_BUDGET_URL}/{user_id}/categories", headers=headers, timeout=8)
        if rc.status_code != 200:
            try:
                error_detail = rc.json().get("detail", rc.text)
            except:
                error_detail = rc.text or f"Status code: {rc.status_code}"
            self.logger.error(
                "Category service error",
                extra={
                    "correlation_id": correlation_id,
                    "url": f"{CATEGORY_BUDGET_URL}/{user_id}/categories",
                    "method": "GET",
                    "status_code": rc.status_code,
                    "detail": error_detail,
                },
            )
            raise ValueError(f"Category service error ({rc.status_code}): {error_detail}")

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
            self.logger.info(
                "Weekly analytics updated",
                extra={
                    "correlation_id": correlation_id,
                    "path": f"/{user_id}/analytics/weekly/last7/recompute",
                    "detail": f"weekly_id={existing['_id']}",
                },
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
        self.logger.info(
            "Weekly analytics generated",
            extra={
                "correlation_id": correlation_id,
                "path": f"/{user_id}/analytics/weekly/last7/generate",
                "detail": f"weekly_id={res.inserted_id}",
            },
        )
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
