import os
import shutil
import uuid
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException, UploadFile
from database.mongo import db
from models.User import UpdateUser

users_db = db['users']
UPLOAD_DIRECTORY = "static/images/users"
API_URL = "http://localhost:8000/static/images/users"

def get_user_by_id(user_id, current_user_role: str):
    if current_user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tiene permiso para acessar"
        )

    try:
        user_data = users_db.find_one({"_id": ObjectId(user_id)})
        if user_data:
            if "password" in user_data:
                del user_data["password"]
            user_data["_id"] = str(user_data["_id"])
            return {
                "message": "Usuario encontrado",
                "data": user_data
            }

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

        for user in users_db.find():
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

def deactivate_user(user_id: str, current_user_role: str):
    if not user_id:
        raise HTTPException(
            status_code=404,
            detail="Id del usuario incorrecto"
        )

    if current_user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tiene permiso para acessar"
        )

    try:
        user_data = users_db.find_one({"_id": ObjectId(user_id)})
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        status = "inactive"

        if user_data["status"] == "inactive":
            status = "active"

        result = users_db.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"status": status}}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado o ya inactivo"
            )

        return {
            "message": f"Usuario {'desactivado' if user_data['status'] == 'active' else 'activado'} correctamente"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_user_data(user_id: str, update_data: UpdateUser, current_user_role: str):
    if current_user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tiene permiso para realizar esta acción"
        )

    try:
        update_fields = update_data.model_dump(exclude_none=True)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar.")

        result = users_db.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {**update_fields, "updated_at": datetime.now(timezone.utc)}}
        )

        if result.modified_count == 0:
            user_exists = users_db.find_one({"_id": ObjectId(user_id)})
            if not user_exists:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            return {"message": "Usuario actualizado exitosamente (sin cambios en los datos)"}

        updated_user = users_db.find_one({"_id": ObjectId(user_id)})
        if "password" in updated_user:
            del updated_user["password"]
        updated_user["_id"] = str(updated_user["_id"])

        return {
            "message": "Usuario actualizado exitosamente",
            "data": updated_user
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al actualizar el usuario: {e}"
        )


async def update_user_files(user_id: str, new_img_upload: UploadFile, current_user_role: str):
    if current_user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tiene permiso para realizar esta acción"
        )

    try:
        user = users_db.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        old_image_url = user.get("profile_picture")
        if old_image_url and API_URL in old_image_url:
            file_path = old_image_url.replace(API_URL + "/", UPLOAD_DIRECTORY + "/")
            if os.path.exists(file_path):
                os.remove(file_path)

        file_ext = os.path.splitext(new_img_upload.filename)[1]
        file_name = f"{uuid.uuid4()}{file_ext}"

        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

        file_path = os.path.join(UPLOAD_DIRECTORY, file_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(new_img_upload.file, buffer)

        new_image_url = f"{API_URL}/{file_name}"

        users_db.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"profile_picture": new_image_url, "updated_at": datetime.now(timezone.utc)}}
        )

        updated_user = users_db.find_one({"_id": ObjectId(user_id)})
        if "password" in updated_user:
            del updated_user["password"]
        updated_user["_id"] = str(updated_user["_id"])

        return {
            "message": "Imagen de perfil actualizada exitosamente",
            "data": updated_user
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al subir la imagen: {e}"
        )