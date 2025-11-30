from fastapi import APIRouter, Path, status, HTTPException, Query, Body
from models.monthly_model import MonthlyGenerateRequest
from services.monthly_service import MonthlyService
from services.weekly_service import WeeklyService

router = APIRouter(prefix="/{user_id}/analytics", tags=["analytics"])

monthly_service = MonthlyService()
weekly_service = WeeklyService()

@router.get("/monthly", status_code=status.HTTP_200_OK)
def get_monthly(user_id: str = Path(...), month: str = Query(...)):
    try:
        return monthly_service.get(user_id, month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/weekly/last7", status_code=status.HTTP_200_OK)
def get_weekly_last7(user_id: str = Path(...)):
    try:
        return weekly_service.get_last7days(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/monthly/generate", status_code=status.HTTP_201_CREATED)
def generate_monthly(user_id: str = Path(...), payload: MonthlyGenerateRequest = Body(...)):
    try:
        return monthly_service.generate(user_id, payload.month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/weekly/last7/generate", status_code=status.HTTP_201_CREATED)
def generate_weekly_last7(user_id: str = Path(...)):
    try:
        return weekly_service.generate_last7days(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/monthly/{month}/recompute", status_code=status.HTTP_200_OK)
def recompute_monthly(user_id: str = Path(...), month: str = Path(...)):
    try:
        return monthly_service.generate(user_id, month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/weekly/last7/recompute", status_code=status.HTTP_200_OK)
def recompute_weekly_last7(user_id: str = Path(...)):
    try:
        return weekly_service.generate_last7days(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/monthly/{month}/delete", status_code=status.HTTP_200_OK)
def delete_monthly(user_id: str = Path(...), month: str = Path(...)):
    try:
        return monthly_service.delete(user_id, month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/weekly/last7/delete", status_code=status.HTTP_200_OK)
def delete_weekly_last7(user_id: str = Path(...)):
    try:
        return weekly_service.delete_last7days(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
