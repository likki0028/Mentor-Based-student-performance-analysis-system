
from pydantic import BaseModel

class StudentBase(BaseModel):
    enrollment_number: str

class StudentCreate(StudentBase):
    user_id: int

class Student(StudentBase):
    id: int
    
    class Config:
        from_attributes = True
