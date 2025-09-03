from models.Cart import Cart, ProductItem
from database.mongo import db

cart_db = db["carts"]

def get_cart(user_id: str):
    cart = cart_db.find_one({"user_id": user_id})
    if cart:
        cart["_id"] = str(cart["_id"])
    return cart

def add_to_cart(product_item: ProductItem, user_id: str):
    cart_data = get_cart(user_id)
    product = product_item.model_dump()
    if cart_data:
        item_found = False
        for item in cart_data["items"]:
            if item["product_id"] == product["product_id"]:
                item["quantity"] = product["quantity"]
                item_found = True
                break

        if not item_found:
            cart_data["items"].append(product)

        cart_db.update_one({"user_id": user_id}, {"$set": {"items": cart_data["items"]}})

    else:
        new_cart = {"user_id": user_id, "items": [product]}
        cart_db.insert_one(new_cart)

    updated_cart = get_cart(user_id)
    updated_cart["_id"] = str(updated_cart["_id"])

    return {
        "message": "Producto añadido al carrito",
        "data": updated_cart
    }

def remove_from_cart(product_id: str, user_id: str,):
    cart_data = get_cart(user_id)
    if cart_data:
        cart_data["items"] = [item for item in cart_data["items"] if item["product_id"] != product_id]
        cart_db.update_one({"user_id": user_id}, {"$set": {"items": cart_data['items']}})

    updated_cart = get_cart(user_id)
    updated_cart["_id"] = str(updated_cart["_id"])

    return {
        "message": "Producto eliminado del carrito",
        "data": updated_cart
    }

def clean_cart(user_id: str):
    cart_db.update_one({"user_id": user_id}, {"$set": {"items": []}})

    return {
        "message": "Carrito eliminado con exito",
    }