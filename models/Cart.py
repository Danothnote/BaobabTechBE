from typing import List
from pydantic import BaseModel

class ProductItem(BaseModel):
    product_id: str
    quantity: int

class Cart(BaseModel):
    user_id: str
    items: List[ProductItem] = []

    class Config:
        arbitrary_types_allowed = True