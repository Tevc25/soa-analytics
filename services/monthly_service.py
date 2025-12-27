import logging
import os
import re
import requests
from datetime import datetime
from db_two.database import get_db
from logging_utils import get_correlation_id

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

CATEGORY_BUDGET_URL = os.getenv("CATEGORY_BUDGET_URL", "http://localhost:8002").rstrip("/")

class MonthlyService:
    def __init__(self):
        self.logger = logging.getLogger("soa-analytics")
        self.db = get_db()
        self.col = self.db["monthly_data"]

    def _month_bounds(self, month: str):
        y = int(month[0:4])
        m = int(month[5:7])
        start = datetime(y, m, 1)
        if m == 12:
            end = datetime(y + 1, 1, 1)
        else:
            end = datetime(y, m + 1, 1)
        return start, end

    def _parse_iso(self, s):
        try:
            return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        except Exception:
            return None

    def generate(self, user_id: str, month: str, jwt_token: str = None):
        if not MONTH_RE.match(month):
            raise ValueError("month must be in YYYY-MM format")

        headers = {}
        correlation_id = get_correlation_id()
        if correlation_id:
            headers["X-Correlation-Id"] = correlation_id
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"

        self.logger.info(
            "Requesting budgets for monthly analytics",
            extra={
                "correlation_id": correlation_id,
                "url": f"{CATEGORY_BUDGET_URL}/{user_id}/budgets",
                "method": "GET",
            },
        )
        rb = requests.get(
            f"{CATEGORY_BUDGET_URL}/{user_id}/budgets",
            params={"month": month},
            headers=headers,
            timeout=8
        )
        if rb.status_code != 200:
            try:
                error_detail = rb.json().get("detail", rb.text)
            except:
                error_detail = rb.text or f"Status code: {rb.status_code}"
            self.logger.error(
                "Budget service error",
                extra={
                    "correlation_id": correlation_id,
                    "url": f"{CATEGORY_BUDGET_URL}/{user_id}/budgets",
                    "method": "GET",
                    "status_code": rb.status_code,
                    "detail": error_detail,
                },
            )
            raise ValueError(f"Budget service error ({rb.status_code}): {error_detail}")

        budgets = rb.json()
        budget_by_cat = {str(b["category_id"]): float(b.get("limit", 0)) for b in budgets}

        self.logger.info(
            "Requesting categories for monthly analytics",
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

        start, end = self._month_bounds(month)
        rows = []

        for c in categories:
            cat_id = str(c.get("category_id"))
            cat_name = c.get("name", "Unknown")

            spent = 0.0
            for it in c.get("items", []) or []:
                dt = self._parse_iso(it.get("created_at"))
                if not dt:
                    continue
                if start <= dt < end:
                    price = float(it.get("item_price", 0))
                    qty = int(it.get("item_quantity", 1))
                    spent += price * qty

            budget = float(budget_by_cat.get(cat_id, 0))

            rows.append({
                "category_id": cat_id,
                "category_name": cat_name,
                "budget": budget,
                "spent": spent
            })

        now = datetime.now()
        existing = self.col.find_one({"user_id": user_id, "month": month})

        if existing:
            self.col.update_one(
                {"_id": existing["_id"]},
                {"$set": {"rows": rows, "updated_at": now}}
            )
            self.logger.info(
                "Monthly analytics updated",
                extra={
                    "correlation_id": correlation_id,
                    "path": f"/{user_id}/analytics/monthly/{month}",
                    "detail": f"monthly_id={existing['_id']}",
                },
            )
            return {"message": "Monthly analytics updated", "monthly_id": str(existing["_id"])}

        doc = {
            "user_id": user_id,
            "month": month,
            "rows": rows,
            "created_at": now,
            "updated_at": now
        }
        res = self.col.insert_one(doc)
        self.logger.info(
            "Monthly analytics generated",
            extra={
                "correlation_id": correlation_id,
                "path": f"/{user_id}/analytics/monthly/generate",
                "detail": f"monthly_id={res.inserted_id}",
            },
        )
        return {"message": "Monthly analytics generated", "monthly_id": str(res.inserted_id)}
    
    def generate_another(self, user_id: str, month: str):
        requests.get("http://localhost:8080/")
        
    def get(self, user_id: str, month: str):
        if not MONTH_RE.match(month):
            raise ValueError("month must be in YYYY-MM format")

        doc = self.col.find_one({"user_id": user_id, "month": month})
        if not doc:
            raise ValueError("Monthly analytics not found")

        return {
            "monthly_id": str(doc["_id"]),
            "user_id": doc["user_id"],
            "month": doc["month"],
            "rows": doc.get("rows", []),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }

    def delete(self, user_id: str, month: str):
        if not MONTH_RE.match(month):
            raise ValueError("month must be in YYYY-MM format")

        res = self.col.delete_one({"user_id": user_id, "month": month})
        if res.deleted_count == 0:
            raise ValueError("Monthly analytics not found")
        return {"message": "Monthly analytics deleted"}
