from fastapi import APIRouter
from models.Category import Category
from services.categories_services import get_categories, add_category, update_category, delete_category

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/")
def get_categories_router():
    return get_categories()

@router.post("/add")
def add_category_router(category: Category):
    return add_category(category)

@router.put("/update/{category_id}")
def update_category_router(category_id: str, new_data: dict):
    return update_category(category_id, new_data)

@router.delete("/delete/{category_id}")
def delete_category_router(category_id: str):
    return delete_category(category_id)