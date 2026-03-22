
from typing import List, Optional
from pydantic import BaseModel

class AssignmentBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    file_url: Optional[str] = None
    subject_id: int
    section_id: Optional[int] = None

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    id: int
    
    class Config:
        from_attributes = True
