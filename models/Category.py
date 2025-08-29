from pydantic import BaseModel
from typing import Optional

class Category(BaseModel):
    name: str
    parent_id: Optional[str] = None