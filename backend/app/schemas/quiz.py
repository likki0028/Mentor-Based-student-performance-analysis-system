
from pydantic import BaseModel

class QuizBase(BaseModel):
    title: str
    subject_id: int
    total_marks: int

class QuizCreate(QuizBase):
    pass

class Quiz(QuizBase):
    id: int
    
    class Config:
        from_attributes = True
