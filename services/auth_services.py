import os
import uuid
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi import HTTPException, status, Response, UploadFile
from fastapi_mail import FastMail, MessageSchema
from mail_server.mail_server import create_reset_token, conf, create_verification_token
from database.mongo import db
from models.User import CreateUser, UserLogin, UpdateUser
import bcrypt
import jwt

users =  db['users']
salt = bcrypt.gensalt()
UPLOAD_DIRECTORY = "static/images/users"
API_URL = "https://back.danosv.com/static/images/users"
fm = FastMail(conf)


def send_verification_email(email: str):
    token = create_verification_token(email)

    verification_link = f"https://baobab.danosv.com/verify-email/{token}"

    html_content = f"""
        <html>
          <body>
            <p>Gracias por registrarte. Haz clic en el siguiente enlace para verificar tu cuenta:</p>
            <p><a href="{verification_link}">Verificar mi Cuenta</a></p>
            <p>Este enlace expirará en 24 horas.</p>
          </body>
        </html>
        """

    message = MessageSchema(
        subject="Verificación de Cuenta",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    try:
        fm.send_message(message)
    except Exception as e:
        print(f"Error al enviar correo de verificación: {e}")

def verify_email(token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        email = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "email_verification":
            raise HTTPException(status_code=400, detail="Token de tipo incorrecto.")

        user = users.find_one({"email": email})

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")

        if user.get("is_verified") is True:
            return {"message": "La cuenta ya estaba verificada."}

        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"is_verified": True}}
        )

        return {"message": "Cuenta verificada exitosamente."}

    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="El token es inválido o ha expirado.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")

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
        user_data["is_verified"] = False

        send_verification_email(user_data["email"])

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

        check = bcrypt.checkpw(
            password= user_login.password.encode("utf8"),
            hashed_password=user_data["password"].encode("utf8")
        )

        if not check:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrecto",
            )

        if not user_data.get("is_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta no ha sido verificada. Por favor, revisa tu correo electrónico."
            )

        if user_data["status"] == "inactive":
            activate = {"status": "active"}
            users.update_one({"_id": user_data["_id"]}, {"$set": activate})

        user_data["_id"] = str(user_data["_id"])

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

def update_user_data(update_data: UpdateUser, user_id):
    try:
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

async def update_user_files(update_data: UploadFile, user_id: str):
    try:
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos para actualizar"
            )

        if not update_data.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser una imagen."
            )

        user_upload_directory = os.path.join(UPLOAD_DIRECTORY, user_id)

        if os.path.exists(user_upload_directory):
            for filename in os.listdir(user_upload_directory):
                file_path = os.path.join(user_upload_directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        os.makedirs(user_upload_directory, exist_ok=True)
        file_extension = os.path.splitext(update_data.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_location = os.path.join(user_upload_directory, unique_filename)

        try:
            with open(file_location, "wb+") as file_object:
                file_object.write(await update_data.read())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al guardar el archivo: {e}"
            )

        new_image_url = f"{API_URL}/{user_id}/{unique_filename}"

        update_fields = {"profile_picture": new_image_url}

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

def forgot_password(request, background_tasks):
    req = request.model_dump()
    email = req["email"]
    user = db["users"].find_one({"email": email})
    if not user:
        return {"message": "Si la cuenta existe, se ha enviado un correo de restablecimiento."}

    expires_minutes= 15
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    reset_token = create_reset_token(email, expires_minutes)

    db["users"].update_one(
        {"email": email},
        {"$set": {"reset_token": reset_token, "reset_token_expires": expires_at}}
    )

    reset_link = f"https://baobab.danosv.com/reset-password/{reset_token}"

    html_content = f"""
        <html>
          <body>
            <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace:</p>
            <p><a href="{reset_link}">Restablecer Contraseña</a></p>
            <p>Este enlace expirará en {expires_minutes} minutos.</p>
          </body>
        </html>
        """

    message = MessageSchema(
        subject="Restablecimiento de Contraseña",
        recipients=[email],
        body=html_content,
        subtype="html"
    )

    background_tasks.add_task(fm.send_message, message)

    return {"message": "Si la cuenta existe, se ha enviado un correo de restablecimiento."}

def reset_password(data):
    user_data = data.model_dump()
    try:
        payload = jwt.decode(user_data["token"], os.getenv("SECRET_KEY"), algorithms=["HS256"])
        email = payload.get("sub")

        user = db["users"].find_one({
            "email": email,
            "reset_token": user_data["token"],
            "reset_token_expires": {"$gt": datetime.now(timezone.utc)}
        })

        if not user:
            raise HTTPException(status_code=400, detail="El token es inválido o ha expirado.")

        hash_password = bcrypt.hashpw(
            password=data.new_password.encode("utf8"),
            salt=salt
        ).decode("utf8")

        db["users"].update_one(
            {"_id": user["_id"]},
            {"$set": {
                "password": hash_password,
                "reset_token": None,
                "reset_token_expires": None
            }}
        )

        return {"message": "Contraseña restablecida exitosamente."}

    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="El token es inválido o ha expirado.")