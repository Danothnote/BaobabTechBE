import os
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from fastapi import HTTPException, status, Response

from database.mongo import db
from models.User import CreateUser, UserLogin, UpdateUser
import bcrypt
import jwt

users =  db['users']
salt = bcrypt.gensalt()

def get_user(current_user):
    try:
        user_data = users.find_one({"_id": ObjectId(current_user["_id"])})
        if user_data:
            if "password" in user_data:
                del user_data["password"]
            user_data["_id"] = str(user_data["_id"])
            return user_data
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido o error en la consulta"
        )

def register_user(create_user: CreateUser):
    try:
        user_data = create_user.model_dump()
        result_exist = users.find_one({"email": user_data["email"]})
        if result_exist:
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Usuario ya existe"
            )

        user_data["role"] = "user"
        user_data["status"] = "active"
        user_data["profile_picture"] = ""

        hash_password = bcrypt.hashpw(
            password= user_data["password"].encode("utf8"),
            salt= salt
        ).decode("utf8")
        user_data["password"] = hash_password
        users.insert_one(user_data)
        return {
            "message": f'Usuario registrado con exito!'
        }
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los datos no son correctos"
        )

def login_user(user_login: UserLogin, response: Response):
    try:
        user_data = users.find_one({"email": user_login.email})

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrecto",
            )

        user_data["_id"] = str(user_data["_id"])

        check = bcrypt.checkpw(
            password= user_login.password.encode("utf8"),
            hashed_password=user_data["password"].encode("utf8")
        )

        if not check:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrecto",
            )

        payload = {
            "_id": user_data["_id"],
            "email": user_data["email"],
            "firstname": user_data["firstname"],
            "lastname": user_data["lastname"],
            "profile_picture": user_data.get("profile_picture", ""),
            "role": user_data["role"],
            "favorite_products": user_data.get("favorite_products", []),
            "exp": datetime.now(timezone.utc) + timedelta(hours=604800)
        }

        encoded_jwt = jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")

        response.set_cookie(
            key="access_token",
            value=f"Bearer {encoded_jwt}",
            httponly=True,
            samesite="lax",
            secure=False,
            expires=604800,
            path="/"
        )

        return {
            "message": f"Bienvenido al sistema {user_data['firstname']} {user_data['lastname']}",
            "user": payload
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {e}"
        )

def logout_user(response: Response):
    try:
        response.delete_cookie(
            key="access_token",
            httponly=True,
            samesite="lax",
            secure=False,
            path="/"
        )
        return {"message": "Sesión cerrada exitosamente"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesión: {e}"
        )

def update_user(current_user: dict, update_data: UpdateUser):
    try:
        user_id = current_user["_id"]
        update_fields = update_data.model_dump(exclude_unset=True)

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos para actualizar"
            )

        if "email" in update_fields:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo electrónico no se debe modificar"
            )

        users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )

        updated_user = users.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"])

        return {
            "message": "Usuario actualizado exitosamente",
            "user": updated_user
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al actualizar el usuario: {e}"
        )