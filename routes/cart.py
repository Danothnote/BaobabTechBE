from fastapi import APIRouter, Depends
from middlewares.auth import get_current_user
from models.Cart import ProductItem
from services.cart_services import get_cart, add_to_cart, remove_from_cart, clean_cart

router = APIRouter(prefix="/cart", tags=["cart"])

@router.get("/")
def get_cart_router(current_user: dict = Depends(get_current_user)):
    cart = get_cart(current_user["_id"])
    return {
        "message": "Carrito de compras",
        "data": cart["items"]
    }

@router.post("/add")
def add_to_cart_router(product_item: ProductItem, current_user: dict = Depends(get_current_user)):
    return add_to_cart(product_item, current_user["_id"])

@router.delete("/remove/{product_id}")
def remove_from_cart_router(product_id: str, current_user: dict = Depends(get_current_user)):
    return remove_from_cart(product_id, current_user["_id"])

@router.delete("/clear")
def clean_cart_router(current_user: dict = Depends(get_current_user)):
    return clean_cart(current_user["_id"])