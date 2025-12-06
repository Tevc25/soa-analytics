from fastapi import APIRouter, Path, status, HTTPException, Query, Body, Depends
from models.monthly_model import MonthlyGenerateRequest
from services.monthly_service import MonthlyService
from services.weekly_service import WeeklyService
from services.auth_service import auth_service, security

router = APIRouter(prefix="/{user_id}/analytics", tags=["analytics"])

monthly_service = MonthlyService()
weekly_service = WeeklyService()

def verify_jwt_token(user_id: str = Path(...), credentials = Depends(security)):
    """
    Dependency function to verify JWT token and validate user_id.
    Returns tuple of (payload, token_string) for forwarding to other services.
    """
    payload = auth_service.get_current_user(credentials)
    token_user_id = payload.get("sub")
    auth_service.validate_user_id(token_user_id, user_id)
    return {"payload": payload, "token": credentials.credentials}

@router.get("/monthly", status_code=status.HTTP_200_OK)
def get_monthly(user_id: str = Path(...), month: str = Query(...), token_data = Depends(verify_jwt_token)):
    try:
        return monthly_service.get(user_id, month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/weekly/last7", status_code=status.HTTP_200_OK)
def get_weekly_last7(user_id: str = Path(...), token_data = Depends(verify_jwt_token)):
    try:
        return weekly_service.get_last7days(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/monthly/generate", status_code=status.HTTP_201_CREATED)
def generate_monthly(user_id: str = Path(...), payload: MonthlyGenerateRequest = Body(...), token_data = Depends(verify_jwt_token)):
    try:
        return monthly_service.generate(user_id, payload.month, token_data["token"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/weekly/last7/generate", status_code=status.HTTP_201_CREATED)
def generate_weekly_last7(user_id: str = Path(...), token_data = Depends(verify_jwt_token)):
    try:
        return weekly_service.generate_last7days(user_id, token_data["token"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/monthly/{month}/recompute", status_code=status.HTTP_200_OK)
def recompute_monthly(user_id: str = Path(...), month: str = Path(...), token_data = Depends(verify_jwt_token)):
    try:
        return monthly_service.generate(user_id, month, token_data["token"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/weekly/last7/recompute", status_code=status.HTTP_200_OK)
def recompute_weekly_last7(user_id: str = Path(...), token_data = Depends(verify_jwt_token)):
    try:
        return weekly_service.generate_last7days(user_id, token_data["token"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/monthly/{month}/delete", status_code=status.HTTP_200_OK)
def delete_monthly(user_id: str = Path(...), month: str = Path(...), token_data = Depends(verify_jwt_token)):
    try:
        return monthly_service.delete(user_id, month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/weekly/last7/delete", status_code=status.HTTP_200_OK)
def delete_weekly_last7(user_id: str = Path(...), token_data = Depends(verify_jwt_token)):
    try:
        return weekly_service.delete_last7days(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
