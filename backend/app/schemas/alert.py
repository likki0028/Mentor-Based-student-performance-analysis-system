
from pydantic import BaseModel
from datetime import datetime

class AlertBase(BaseModel):
    message: str
    type: str

class AlertCreate(AlertBase):
    student_id: int

class Alert(AlertBase):
    id: int
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
