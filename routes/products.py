from fastapi import APIRouter, Depends, Form, UploadFile, File
from middlewares.auth import get_current_user
from typing import List, Optional
from models.Product import Product, ProductUpdate
from services.products_services import create_product, get_all_products, get_product_by_id, get_products_by_filter, get_owner_products, update_product, delete_product

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/")
def get_all_products_router():
    return get_all_products()

@router.get("/by_id/{_id}")
def get_product_by_id_router(_id: str):
    return get_product_by_id(_id)

@router.get("/by_filter")
def get_products_by_filter_router(filter_product: dict):
    return get_products_by_filter(filter_product)

@router.get("/owner_products")
def get_owner_products_router(current_user: dict = Depends(get_current_user)):
    return get_owner_products(current_user["_id"])

@router.post("/")
async def create_product_router(
        product_name: str = Form(...),
        description: str = Form(...),
        brand: str = Form(...),
        model: str = Form(...),
        category: str = Form(...),
        image_url: List[UploadFile] = File(None),
        price: float = Form(...),
        quantity: int = Form(...),
        cpu: Optional[str] = Form(None),
        gpu: Optional[str] = Form(None),
        ram: Optional[int] = Form(None),
        storage_type: Optional[str] = Form(None),
        storage: Optional[int] = Form(None),
        battery: Optional[int] = Form(None),
        display_size: Optional[float] = Form(None),
        display_resolution: Optional[str] = Form(None),
        panel_type: Optional[str] = Form(None),
        current_user: dict = Depends(get_current_user)
):
    product_data = Product(
        product_name=product_name,
        description=description,
        brand=brand,
        model=model,
        category=category,
        image_url=[],
        price=price,
        quantity=quantity,
        cpu=cpu,
        gpu=gpu,
        ram=ram,
        storage_type=storage_type,
        storage=storage,
        battery=battery,
        display_size=display_size,
        display_resolution=display_resolution,
        panel_type=panel_type
    )
    return await create_product(product_data, image_url, current_user["_id"])

@router.patch("/{_id}")
async def update_product_router(
        _id: str,
        update_data: ProductUpdate,
        new_img_upload: Optional[List[UploadFile]],
        current_user: dict = Depends(get_current_user)
):
    return await update_product(_id, update_data, new_img_upload, current_user["_id"])

@router.delete("/{_id}")
def delete_product_router(_id: str, current_user: dict = Depends(get_current_user)):
    return delete_product(_id, current_user["_id"])