from fastapi import APIRouter, Depends
from middlewares.auth import get_current_user
from services.users_services import get_all_users, get_user_by_id, deactivate_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def get_users_router(current_user: dict = Depends(get_current_user)):
    return get_all_users(current_user["role"])

@router.get("/by_id/{user_id}")
def get_user_by_id_router(user_id: str, current_user: dict = Depends(get_current_user)):
    return get_user_by_id(user_id, current_user["role"])

@router.patch("/deactivate/{user_id}")
def deactivate_user_router(user_id:str, current_user: dict = Depends(get_current_user)):
    return deactivate_user(user_id, current_user["role"])