from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, UploadFile
from database.mongo import db
from models.Product import Product, ProductUpdate
from typing import List, Optional
import os
import shutil
import uuid

products = db["products"]
UPLOAD_DIRECTORY = "static/images/products"
API_URL = "http://localhost:8000/static/images/products"

def generate_sku(new_product: Product):
    sku_parts = [
        new_product["category"].upper(),
        new_product["brand"].upper(),
        new_product["model"].upper()
    ]

    special_categories = {"laptop", "desktop_pc", "cellphone"}

    if new_product["category"] in special_categories:
        if new_product.get("cpu"):
            sku_parts.append(new_product["cpu"].upper())
        if new_product.get("gpu"):
            sku_parts.append(new_product["gpu"].upper())
        if new_product.get("ram"):
            sku_parts.append(f"{new_product['ram']}GB")
        if new_product.get("storage"):
            sku_parts.append(f"{new_product['storage']}GB")
        if new_product.get("display_size"):
            sku_parts.append(f"{new_product['display_size']}IN")
        if new_product.get("panel_type"):
            sku_parts.append(new_product["panel_type"].upper())

    return "-".join(part for part in sku_parts if part)

def get_all_products():
    try:
        results = []

        for product in products.find():
            product["_id"] = str(product["_id"])
            results.append(product)

        if not results:
            return {
                "message": "Productos no encontrados",
                "data": []
            }

        return {
            "message": "Productos encontrados",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_owner_products(owner: str):
    try:
        results = []

        for product in products.find({"owner": owner}):
            product["_id"] = str(product["_id"])
            results.append(product)

        return {
            "message": "Productos encontrados",
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_product_by_id(product_id):
    try:
        result_exists = products.find_one({"_id": ObjectId(product_id)})

        if not result_exists:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        result_exists["_id"] = str(result_exists["_id"])

        return {
            "message": "Producto encontrado",
            "data": result_exists
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_products_by_filter(filter_product: dict):
    try:
        results = []

        for product in products.find(filter_product):
            product["_id"] = str(product["_id"])
            results.append(product)

        if not results:
            return {
                "message": "Productos no encontrados",
                "data": []
            }

        return {
            "message": "Productos encontrados",
            "data": results
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_product(product: Product, upload_files: List[UploadFile], owner: str):
    try:
        new_product = product.model_dump(exclude_none=True)
        new_product["sku"] = generate_sku(new_product)

        result_exists = products.find_one({"sku": new_product["sku"]})

        if result_exists:
            raise HTTPException(
                status_code=409,
                detail="El producto ya existe"
            )

        new_product["owner"] = owner
        new_product["created_at"] = datetime.now()

        result = products.insert_one(new_product)
        new_product_id = result.inserted_id

        image_paths = []

        user_upload_directory = os.path.join(UPLOAD_DIRECTORY, owner, str(new_product_id))
        os.makedirs(user_upload_directory, exist_ok=True)

        for image_file in upload_files:
            file_extension = os.path.splitext(image_file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_location = os.path.join(user_upload_directory, unique_filename)

            with open(file_location, "wb+") as file_object:
                file_object.write(await image_file.read())

            image_paths.append(f"{API_URL}/{owner}/{new_product_id}/{unique_filename}")

        products.update_one(
            {"_id": new_product_id},
            {"$set": {"image_url": image_paths}}
        )
        return {
            "message": 'Producto registrado con exito!'
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def update_product(product_id: str, update_data: ProductUpdate, new_uploaded_files: Optional[List[UploadFile]], owner: str):
    try:
        update_fields = update_data.model_dump(exclude_unset=True)
        product = products.find_one({"_id": ObjectId(product_id)})

        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if not update_fields:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")

        #if not product["owner"] == owner:
        #    raise HTTPException(status_code=401, detail="Usuario no autorizado")

        current_img_upload_urls = set(product.get("image_url", []))
        desired_img_upload_urls = set(update_data) if update_data.image_url is not None else set(current_img_upload_urls)

        for url in current_img_upload_urls:
            if url not in desired_img_upload_urls:
                try:
                    relative_path = url.replace(f"{API_URL}/", "")
                    parts = relative_path.split('/')
                    if len(parts) == 3:
                        owner_folder, product_id_folder, filename = parts
                        file_path_to_delete = os.path.join(UPLOAD_DIRECTORY, owner_folder, product_id_folder, filename)
                        if os.path.exists(file_path_to_delete):
                            os.remove(file_path_to_delete)
                            print(f"Archivo eliminado: {file_path_to_delete}")
                        else:
                            raise HTTPException(status_code=404, detail=f"No se encontró el archivo para eliminar: {file_path_to_delete}")
                    else:
                        raise HTTPException(status_code=404, detail=f"Advertencia: No se pudo analizar la URL para la eliminación: {url}")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error al eliminar el archivo {url}: {e}")

        new_image_urls = []
        if new_uploaded_files:
            product_obj_id = str(product["_id"])
            user_upload_directory = os.path.join(UPLOAD_DIRECTORY, owner, product_obj_id)
            os.makedirs(user_upload_directory, exist_ok=True)

            for image_file in new_uploaded_files:
                file_extension = os.path.splitext(image_file.filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_location = os.path.join(user_upload_directory, unique_filename)

                with open(file_location, "wb+") as file_object:
                    file_object.write(await image_file.read())

                new_image_urls.append(f"{API_URL}/{owner}/{product_obj_id}/{unique_filename}")

        final_img_upload_list = list(desired_img_upload_urls.union(set(new_image_urls)))

        update_fields["image_url"] = final_img_upload_list

        products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_fields}
        )

        updated_product = products.find_one({"_id": ObjectId(product_id)})
        updated_product["_id"] = str(updated_product["_id"])

        return {
            "message": "Producto actualizado exitosamente",
            "flat": updated_product
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor al actualizar el producto: {e}"
        )

def delete_product(product_id: str, user_id: str):
    try:
        product = products.find_one({"_id": ObjectId(product_id)})
        owner_id = product["owner"]

        if not product:
            raise HTTPException(
                status_code=400,
                detail="No existe el producto"
            )

        if not owner_id == user_id:
            raise HTTPException(
                status_code=401,
                detail="El usuario no es el dueño del producto"
            )

        product_image_directory = os.path.join(UPLOAD_DIRECTORY, owner_id, product_id)
        if os.path.exists(product_image_directory):
            try:
                shutil.rmtree(product_image_directory)
            except OSError as e:
                print(f"Error al eliminar el directorio del producto {product_image_directory}: {e}")

        result = products.delete_one({"_id": ObjectId(product_id)})

        return {
            "message": "Producto borrado exitosamente",
            "data": result.deleted_count
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor al borrar el producto: {e}"
        )

def update_product_data(product_id: str, update_data: ProductUpdate, user_id: str):
    try:
        update_fields = update_data.model_dump(exclude_unset=True)
        product = products.find_one({"_id": ObjectId(product_id)})

        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if not update_fields:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")

        sku_modified = False
        sku_relevant_fields = ["category", "brand", "model", "cpu", "gpu", "ram", "storage", "display_size",
                               "panel_type"]

        for field in sku_relevant_fields:
            if field in update_fields and update_fields[field] != product.get(field):
                sku_modified = True
                break

        if sku_modified:
            updated_product_data = product.copy()
            updated_product_data.update(update_fields)

            new_sku = generate_sku(updated_product_data)

            if products.find_one({"sku": new_sku, "_id": {"$ne": ObjectId(product_id)}}):
                raise HTTPException(status_code=409, detail="El nuevo SKU del producto ya existe")

            update_fields["sku"] = new_sku

        products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_fields}
        )

        updated_product = products.find_one({"_id": ObjectId(product_id)})
        updated_product["_id"] = str(updated_product["_id"])

        return {
            "message": "Producto actualizado exitosamente",
            "flat": updated_product
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor al actualizar el producto: {e}"
        )

async def update_product_files(
        product_id: str,
        new_img_upload: Optional[List[UploadFile]],
        images_to_delete: Optional[List[str]],
        user_id: str
):
    try:
        product = products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if product.get("owner") != user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este producto")

        if images_to_delete:
            for url in images_to_delete:
                file_path = url.replace(API_URL + "/", UPLOAD_DIRECTORY + "/")
                if os.path.exists(file_path):
                    os.remove(file_path)

        new_image_urls = []
        if new_img_upload:
            for file in new_img_upload:
                file_ext = os.path.splitext(file.filename)[1]
                file_name = f"{uuid.uuid4()}{file_ext}"
                file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                new_image_urls.append(f"{API_URL}/{file_name}")

        current_images = [url for url in product.get("image_url", []) if url not in images_to_delete]
        updated_image_urls = current_images + new_image_urls

        products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"image_url": updated_image_urls, "updated_at": datetime.utcnow()}}
        )

        updated_product = products.find_one({"_id": ObjectId(product_id)})
        updated_product["_id"] = str(updated_product["_id"])

        return {
            "message": "Imágenes del producto actualizadas exitosamente",
            "data": updated_product
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor al actualizar las imágenes: {e}"
        )