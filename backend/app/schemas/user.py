
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    LECTURER = "lecturer"
    MENTOR = "mentor"
    STUDENT = "student"
    BOTH = "both"

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    role: UserRole

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
