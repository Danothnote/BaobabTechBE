from bson import ObjectId
from fastapi import HTTPException
from database.mongo import db
from typing import List

favorites_db = db["favorites"]

def get_user_favorites(user_id: str):
    try:
        favorites = favorites_db.find_one({"owner": user_id})
        if not favorites:
            user_favorites = {
                "owner": user_id,
                "favorites": []
            }
            favorites_db.insert_one(user_favorites)
            favorites_data = favorites_db.find_one({"owner": user_id})
            favorites_data["_id"] = str(favorites_data["_id"])
            return {
                "message": "Datos actualizados",
                "data": favorites_data["favorites"]
            }
        favorites["_id"] = str(favorites["_id"])
        return {
            "message": "Favoritos encontrados",
            "data": favorites["favorites"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def set_user_favorites(favorites, user_id: str):
    if not favorites.product_id:
        raise HTTPException(
            status_code=400,
            detail="No hay datos para actualizar"
        )

    try:
        if favorites.action == "add":
            update_operator = {"$addToSet": {"favorites": favorites.product_id}}
        elif favorites.action == "remove":
            update_operator = {"$pull": {"favorites": favorites.product_id}}
        else:
            raise HTTPException(status_code=400, detail="Acción no válida. Usa 'add' o 'remove'.")

        favorites_data = favorites_db.find_one({"owner": user_id})
        favorites_db.update_one(
            {"_id": favorites_data.get("_id")},
            update_operator
        )

        return {
            "message": f"Producto '{favorites.product_id}' {'agregado' if favorites.action == 'add' else 'eliminado'} exitosamente."
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))