from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from middlewares.auth import get_current_user
from models.User import UpdateUser
from services.users_services import get_all_users, get_user_by_id, deactivate_user, update_user_data, update_user_files

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


@router.patch("/by_id/data/{user_id}")
def update_user_data_router(
        user_id: str,
        update_data: UpdateUser,
        current_user: dict = Depends(get_current_user)
):
    return update_user_data(user_id, update_data, current_user["role"])


@router.patch("/by_id/files/{user_id}")
async def update_user_files_router(
        user_id: str,
        new_img_upload: Optional[UploadFile] = File(None),
        current_user: dict = Depends(get_current_user)
):
    if not new_img_upload:
        raise HTTPException(status_code=400, detail="Se requiere una imagen para actualizar.")

    return await update_user_files(user_id, new_img_upload, current_user["role"])