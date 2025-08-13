from fastapi import APIRouter, Depends
from middlewares.auth import get_current_user
from models.Favorite import Favorite
from services.favorites_services import get_user_favorites, set_user_favorites

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.get("/")
def get_user_favorites_router(current_user: dict = Depends(get_current_user)):
    return get_user_favorites(current_user["_id"])

@router.put("/update")
def set_user_favorites_router(favorites: Favorite, current_user: dict = Depends(get_current_user)):
    return set_user_favorites(favorites, current_user["_id"])