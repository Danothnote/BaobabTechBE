from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class CreateUser(BaseModel):
    firstname: str
    lastname: str
    email: str
    birth_date: datetime
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UpdateUser(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    profile_picture: Optional[str] = None
    favorite_products: Optional[List[str]] = None