
from pydantic import BaseModel
from datetime import date

class AssignmentBase(BaseModel):
    title: str
    description: str
    due_date: date
    subject_id: int

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    id: int
    
    class Config:
        from_attributes = True
