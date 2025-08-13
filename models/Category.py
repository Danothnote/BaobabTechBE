from bson import ObjectId
from pydantic import BaseModel
from typing import List, Optional


class Category(BaseModel):
    name: str
    parent_id: Optional[str] = None