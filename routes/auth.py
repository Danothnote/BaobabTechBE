from fastapi import APIRouter, Response, Depends, File, UploadFile, BackgroundTasks
from models.User import CreateUser, UserLogin, UpdateUser, ForgotPasswordRequest, ResetPasswordData
from services.auth_services import register_user, login_user, get_user, logout_user, update_user_data, update_user_files, forgot_password, reset_password, verify_email
from middlewares.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me")
def get_user_router(current_user: dict = Depends(get_current_user)):
    return get_user(current_user)

@router.post("/signup")
def register_user_router(create_user: CreateUser):
    return register_user(create_user)

@router.post("/verify-email/{token}")
def verify_email_router(token: str):
    return verify_email(token)

@router.post("/login")
def login_user_router(user_login: UserLogin, response: Response):
    return login_user(user_login, response)

@router.post("/logout")
def logout_user_router(response: Response):
    return logout_user(response)

@router.patch("/me/data")
def update_user_data_router(update_data: UpdateUser, current_user: dict = Depends(get_current_user)):
    return update_user_data(update_data, current_user["_id"])

@router.patch("/me/files")
async def update_user_data_router(new_img_upload: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    return await update_user_files(new_img_upload, current_user["_id"])

@router.post("/forgot-password")
def forgot_password_router(request: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    return forgot_password(request, background_tasks)

@router.post("/reset-password")
def reset_password_router(data: ResetPasswordData):
    return reset_password(data)