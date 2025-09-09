from typing import Optional
from pydantic import BaseModel
from uuid import UUID


class UserSchema(BaseModel):
    id: Optional[UUID] = None
    first_name: str
    second_name: str
    last_name: str
    login: str
    password: Optional[str] = None
    photo: Optional[str] = None
