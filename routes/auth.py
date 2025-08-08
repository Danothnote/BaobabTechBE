from fastapi import APIRouter, Response, Depends
from models.User import CreateUser, UserLogin, UpdateUser
from services.auth_services import register_user, login_user, get_user, logout_user, update_user
from middlewares.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me")
def get_user_router(current_user: dict = Depends(get_current_user)):
    return get_user(current_user)

@router.post("/signup")
def register_user_router(create_user: CreateUser):
    return register_user(create_user)

@router.post("/login")
def login_user_router(user_login: UserLogin, response: Response):
    return login_user(user_login, response)

@router.post("/logout")
def logout_user_router(response: Response):
    return logout_user(response)

@router.patch("/me")
def update_user_router(update_data: UpdateUser, current_user: dict = Depends(get_current_user)):
    return update_user(current_user, update_data)