from bson import ObjectId
from fastapi import HTTPException

from database.mongo import db
from models.Category import Category

categories_db = db["categories"]

def get_categories():
    try:
        results = []

        for category in categories_db.find({"parent_id": {"$exists": False}}):
            category["_id"] = str(category["_id"])
            subcategories = []
            for subcategory in categories_db.find({"parent_id": category["_id"]}):
                subcategory["_id"] = str(subcategory["_id"])
                subcategories.append(subcategory)
            category_data = {
                "_id": category["_id"],
                "name": category["name"],
                "subcategories": subcategories,
            }
            results.append(category_data)

        return {
            "message": "Categorías encontradas",
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def add_category(category: Category):
    try:
        category_data = category.model_dump(exclude_none=True)

        if not category_data:
            raise HTTPException(
                status_code=400,
                detail="Por favor ingrese los datos correctamente"
            )

        result_exists = categories_db.find_one({"name": category_data["name"]})

        if result_exists:
            raise HTTPException(
                status_code=409,
                detail="La categoría ya existe"
            )

        categories_db.insert_one(category_data)

        return {
            "message": "Datos ingresados correctamente",
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def update_category(category_id: str, new_data: dict):
    try:
        if not category_id:
            raise HTTPException(
                status_code=404,
                detail="ID de la categoría incorrecto"
            )

        if not new_data:
            raise HTTPException(
                status_code=400,
                detail="No existen datos para actualizar"
            )

        update_query = {"$set": new_data}

        if "parent_id" in new_data and new_data["parent_id"] is None:
            del new_data["parent_id"]
            update_query["$unset"] = {"parent_id": ""}

        categories_db.update_one(
            {"_id": ObjectId(category_id)},
            update_query
        )

        return {
            "message": "Datos actualizados correctamente",
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def delete_category(category_id: str):
    try:
        if not category_id:
            raise HTTPException(
                status_code=404,
                detail="ID de la categoría incorrecto"
            )

        categories_db.delete_many({"parent_id": category_id})
        categories_db.delete_one({"_id": ObjectId(category_id)})
        return {
            "message": "Categoría eliminada"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))