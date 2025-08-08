from bson import ObjectId
from fastapi import HTTPException, status
from database.mongo import db

users = db['users']

def get_user_by_id(user_id, current_user_role: str):
    if current_user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tiene permiso para acessar"
        )
    try:
        user_data = users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            if "password" in user_data:
                del user_data["password"]
            user_data["_id"] = str(user_data["_id"])
            return user_data
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"ID de usuario inválido o error en la consulta: {e}"
        )

def get_all_users(current_user_role: str):
    if current_user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tiene permiso para acessar"
        )
    try:
        results = []

        for user in users.find():
            user["_id"] = str(user["_id"])
            if "password" in user:
                del user["password"]
            results.append(user)

        return {
            "message": "Usuarios encontrados",
            "data": results
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
