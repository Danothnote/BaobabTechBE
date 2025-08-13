from typing import Literal
from pydantic import BaseModel

class Favorite(BaseModel):
    product_id: str
    action: Literal["add", "remove"]