from typing import Optional, List
from pydantic import BaseModel
from fastapi import Form

class Product(BaseModel):
    product_name: str
    description: str
    brand: str
    model: str
    category: str
    image_url: List[str]
    price: float
    quantity: int
    cpu: Optional[str] = None
    gpu: Optional[str] = None
    ram: Optional[int] = None
    storage_type: Optional[str] = None
    storage: Optional[int] = None
    battery: Optional[int] = None
    display_size: Optional[float] = None
    display_resolution: Optional[str] = None
    panel_type: Optional[str] = None

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[List[str]] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    cpu: Optional[str] = None
    gpu: Optional[str] = None
    ram: Optional[int] = None
    storage_type: Optional[str] = None
    storage: Optional[int] = None
    battery: Optional[int] = None
    display_size: Optional[float] = None
    display_resolution: Optional[str] = None
    panel_type: Optional[str] = None
